from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from authentication.models import get_or_create_customer, get_or_create_connect_account
from Hotel.models import RoomType, Hotel
from Hotel.views import IsHotelier
from .models import *
from .serializers import *
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY
stripe_webhook_secret = settings.STRIPE_WEBHOOK_SECRET

# Create your views here.


class IsCustomer(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_authenticated:
            return request.user and request.user.is_customer
        else:
            return False


class CardsViewSet(viewsets.ViewSet):
    permission_classes = (IsCustomer,)

    def list(self, request):
        customer, create = get_or_create_customer(request.user)
        if not create:
            try:
                payment_methods = customer.list_payment_methods()
            except Exception as err:
                return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)
            else:
                if payment_methods.data:
                    return Response(payment_methods, status=status.HTTP_200_OK)

        return Response({"detail": "No card found associated with this customer"}, status=status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, pk):
        customer, create = get_or_create_customer(request.user)
        detail = "No card found associated with this customer"
        if not create:
            try:
                payment_method = customer.retrieve_payment_method(pk)
            except stripe.error.InvalidRequestError as ire:
                detail = str(ire)
            except Exception as err:
                return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(payment_method, status=status.HTTP_200_OK)

        return Response({"detail": detail}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        try:
            customer, _ = get_or_create_customer(request.user)
            setup_intent = stripe.SetupIntent.create(
                customer=customer.id,
                payment_method_types=["card"],
            )
        except Exception as err:
            return Response({"detail", str(err)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"clientSecret": setup_intent.client_secret})

    def destroy(self, request, pk):
        try:
            customer, _ = get_or_create_customer(request.user)
            customer.retrieve_payment_method(pk)
        except Exception:
            return Response({"detail": "sw"}, status=status.HTTP_404_NOT_FOUND)
        else:
            stripe.PaymentMethod.detach(pk)

        return Response(status=status.HTTP_204_NO_CONTENT)


class ReservationViewSet(viewsets.ViewSet):
    permission_classes = (IsCustomer,)

    @staticmethod
    def __create(customer_id: str, data: dict) -> tuple[bool, dict]:
        """
        created: bool, data: serializer.data | serializer.errors = create(data)\n
        customer_id => "4bffd9df-3afe-4692-ab0a-559556dc5e27"\n
        data => {
            "hotel": "812e5a62-5a4f-46b6-817d-72a9d73a41ed",
            "name": "username",
            "email": "user@email.com",
            "phone": "9133455783",
            "checkin": "2024-04-01",
            "checkout": "2024-04-03",
            "bedrooms": [
                {"room_type": "3daae506-e87b-473d-a639-b762b01d0a08", "rooms": 3},
                {"room_type": "cbc9ed75-5a98-4485-920a-359e56a2a2cd", "rooms": 1},
            ],
        }
        """
        def validate_customer_rooms(bedrooms: dict, checkin: str, checkout: str):
            for room in bedrooms:
                rooms_available = room["room_type"].get_rooms_available(checkin, checkout)
                if rooms_available["rooms_available"] < room["rooms"]:
                    return False, {"detail": f"The room type `{rooms_available['type']}` does not have enough rooms."}
            return (True,)

        data["customer"] = customer_id
        serializer = ReservationSerializer(data=data)
        if serializer.is_valid():
            validate_customer_rooms_ = validate_customer_rooms(
                bedrooms=serializer.validated_data["bedrooms"],
                checkin=serializer.validated_data["checkin"],
                checkout=serializer.validated_data["checkout"],
            )
            if not validate_customer_rooms_[0]:
                return False, validate_customer_rooms_[1]
            serializer.save()
            return True, serializer.data
        else:
            return False, serializer.errors

    @staticmethod
    def __get_payment_amount(data: dict) -> tuple[int, int]:
        """
        Returns the price in cents and the amount of the fee\n
        amount: int, fee_amount: int = __get_payment_amount(data)\n
        data => {
            "checkin": "2024-04-01",
            "checkout": "2024-04-03",
            "bedrooms": [
                {"room_type": "3daae506-e87b-473d-a639-b762b01d0a08", "rooms": 3},
                {"room_type": "cbc9ed75-5a98-4485-920a-359e56a2a2cd", "rooms": 1},
            ],
        }
        """
        bedrooms = data.get("bedrooms")
        price = sum([RoomType.objects.get(id=i['room_type']).price * i['rooms'] for i in bedrooms])
        listdate1 = data.get("checkin").split("-")
        listdate2 = data.get("checkout").split("-")
        date1 = timezone.datetime(int(listdate1[0]), int(listdate1[1]), int(listdate1[2]))
        date2 = timezone.datetime(int(listdate2[0]), int(listdate2[1]), int(listdate2[2]))
        days = (date2 - date1).days
        amount = int(price * days * 100)
        fee_amount = int(amount * settings.APPLICATION_FEE_AMOUNT)
        return amount, fee_amount

    @staticmethod
    def __get_the_hotelier_is_connected_account(hotel_id):
        hotel = Hotel.objects.get(id=hotel_id)
        return hotel.hotelier.connect_account

    def check_if_a_room_is_available(self, request, *args, **kwargs):
        try:
            # id_hotel,  date_from, date_to are required parameters in the query params
            hotel_id = request.query_params.get("id_hotel")
            if not hotel_id:
                raise ValueError("Missing parameter `id_hotel`")

            date_from = request.query_params.get("date_from")
            date_to = request.query_params.get("date_to")

            if not all([date_from, date_to]):
                raise ValueError("Missing parameters `date_from` or `date_to`")

            try:
                date_format = "%Y-%m-%d"
                from_date = timezone.datetime.strptime(date_from, date_format).date()
                to_date = timezone.datetime.strptime(date_to, date_format).date()
            except ValueError:
                raise ValueError("Incorrect data format for `date_from` and/or `date_to`. Expected YYYY-MM-DD.")
        except ValueError as err:
            return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            room_availability = Hotel.objects.get(id=hotel_id).check_room_availability(from_date, to_date)
            return Response(room_availability)

    def payment_with_new_card(self, request):
        try:
            customer, _ = get_or_create_customer(request.user)

            create, data = self.__create(customer.id, request.data)
            if not create:
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            amount, fee_amount = self.__get_payment_amount(data)
            hotelier_account = self.__get_the_hotelier_is_connected_account(data.get("hotel"))

            intent = stripe.PaymentIntent.create(
                customer=customer.id,
                setup_future_usage=settings.PAYMENT_INTENT_SETUP_FUTURE_USED,
                amount=amount,
                currency=settings.CURRENCY_CODE,
                metadata={"order_id": data.get("id")},
                receipt_email=data.get("email"),
                description=f"Reservation {data.get('id')}",
                #statement_descriptor=settings.STATEMENT_DESCRIPTOR,
                #statement_descriptor_suffix=settings.STATEMENT_DESCRIPTRIPTOR_SUFFIX,
                transfer_data={'destination': hotelier_account},
                application_fee_amount=fee_amount,
            )
        except Exception as err:
            return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"clientSecret": intent.client_secret}, status=status.HTTP_200_OK)

    def payment_with_saved_card(self, request):
        try:
            customer, _ = get_or_create_customer(request.user)

            payment_method = customer.retrieve_payment_method(request.data.pop("payment_method_id"))
            create, data = self.__create(customer.id, request.data)
            if not create:
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            amount, fee_amount = self.__get_payment_amount(data)
            hotelier_account = self.__get_the_hotelier_is_connected_account(data.get("hotel"))

            intent = stripe.PaymentIntent.create(
                customer=customer.id,
                amount=amount,
                currency=settings.CURRENCY_CODE,
                payment_method=payment_method.id,
                metadata={"order_id": data.get("id")},
                receipt_email=data.get("email"),
                description=f"Reservation {data.get('id')}",
                #statement_descriptor=settings.STATEMENT_DESCRIPTOR,
                #statement_descriptor_suffix=settings.STATEMENT_DESCRIPTRIPTOR_SUFFIX,
                confirm=True,
                off_session=True,
                transfer_data={'destination': hotelier_account},
                application_fee_amount=fee_amount,
            )
        except stripe.error.CardError as ce:
            return Response({"detail": str(ce)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as err:
            return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"clientSecret": intent.client_secret})


class ReservationReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationReadOnlySerializer
    permission_classes = (IsCustomer, IsHotelier)
    pagination_class = PageNumberPagination
    pagination_class.page_size = 9

    filter_backends = [DjangoFilterBackend]

    filterset_fields = {
        "status": ["exact"]
    }

    def get_queryset(self):
        if self.request.user.is_hotelier:
            hotels = Hotel.objects.filter(hotelier=self.request.user.id)
            return Reservation.objects.filter(hotel__in=hotels)
        else:
            return Reservation.objects.filter(customer=self.request.user.id)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        page = self.paginate_queryset(queryset)   # Aplica la paginación
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response(serializer.data)
    
    def retrieve(self, request, pk, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(id=pk)
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)


class PaymentEventViewSet(viewsets.ViewSet):

    @staticmethod
    def __comfirm_payment(payment_intent: stripe.PaymentIntent) -> None:
        metadata = payment_intent.metadata
        order_id = metadata.get("order_id")
        reservation = Reservation.objects.get(id=order_id)
        reservation.payment_intent = payment_intent.id
        reservation.amount = payment_intent.amount / 100
        reservation.status = "RE"
        reservation.save()

    def handle_payment_event(self, request, *args, **kwargs):
        event = None
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig_header,
                secret=stripe_webhook_secret
            )
        except ValueError as err:
            print(err)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as err:
            print(err)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if event.type == "payment_intent.succeeded":
            self.__comfirm_payment(event.data.object)

        elif event.type == "payment_intent.requires_action":
            pass
        elif event.type == "payment_intent.partially_funded":
            pass
        elif event.type.startswith("setup_intent"):
            print(event.type)
            setup_intent = event.data.object
            print(setup_intent)
        elif event.type == "charge.refunded":
            pass
        else:
            print(f"Event not handled: {event.type}")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)



class AccountLinkGenerationViewSet(viewsets.ViewSet):
    permission_classes = (IsHotelier,)

    def generate_account_link(self, request, *args, **kwargs):
        try:
            refresh_url = request.data.get("refresh")
            redirect_url = request.data.get("redirect")
            connect_account, _ = get_or_create_connect_account(request.user)
            link = stripe.AccountLink.create(
                account=connect_account,
                refresh_url=refresh_url,
                return_url=redirect_url,
                type="account_onboarding"
            )
        except Exception as err:
            return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'link': link.url})
    
    def generate_dashboard_stripe_link(self, request, *args, **kwargs):
        try:
            hotelier_account = request.user.hoteliers.connect_account
            link = stripe.Account.create_login_link(hotelier_account)
        except Exception as err:
            Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'link': link.url})
