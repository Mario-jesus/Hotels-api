from django.urls import path
from .views import *

urlpatterns = [
    path("room_availability/", ReservationViewSet.as_view({"get": "check_if_a_room_is_available"})),
    path("reservations/new_card/", ReservationViewSet.as_view({"post": "payment_with_new_card"})),
    path("reservations/saved_card/", ReservationViewSet.as_view({"post": "payment_with_saved_card"})),
    path("reservations/", ReservationReadOnlyViewSet.as_view({"get": "list"})),
    path("reservations/<slug:pk>/", ReservationReadOnlyViewSet.as_view({"get": "retrieve"})),
    path("cards/", CardsViewSet.as_view({
        "post": "create",
        "get": "list",
    })),
    path("cards/<slug:pk>/", CardsViewSet.as_view({
        "get": "retrieve",
        "delete": "destroy",
    })),
    path("generate_account_link/", AccountLinkGenerationViewSet.as_view({"post": "generate_account_link"})),
    path("generate_dashboard_stripe_link/", AccountLinkGenerationViewSet.as_view({"get": "generate_dashboard_stripe_link"})),
    path("handle-payment-event/", PaymentEventViewSet.as_view(
        {"post": "handle_payment_event"}),
        name="handle-payment-event",
    ),
]
