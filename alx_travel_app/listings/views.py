import requests
import json
from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Booking, Payment
from .serializers import PaymentSerializer

class InitiatePaymentView(APIView):
    def post(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id, user=request.user)
            
            # Check if payment already exists
            if hasattr(booking, 'payment'):
                return Response(
                    {'error': 'Payment already initiated for this booking'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Prepare Chapa payment data
            chapa_url = "https://api.chapa.co/v1/transaction/initialize"
            headers = {
                "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "amount": str(booking.total_price),
                "currency": "ETB",
                "email": request.user.email,
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "tx_ref": f"booking_{booking.id}",
                "callback_url": f"{settings.BASE_URL}/api/payments/verify/{booking.id}/",
                "return_url": f"{settings.FRONTEND_URL}/bookings/{booking.id}/payment-complete/",
                "customization": {
                    "title": "ALX Travel App",
                    "description": "Booking Payment"
                }
            }

            # Make request to Chapa API
            response = requests.post(chapa_url, headers=headers, data=json.dumps(payload))
            response_data = response.json()

            if response.status_code == 200 and response_data['status'] == 'success':
                # Create payment record
                payment = Payment.objects.create(
                    booking=booking,
                    amount=booking.total_price,
                    transaction_id=response_data['data']['tx_ref'],
                    chapa_response=response_data
                )

                return Response({
                    'payment_url': response_data['data']['checkout_url'],
                    'payment_id': payment.id,
                    'status': 'Payment initiated successfully'
                }, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': 'Failed to initiate payment', 'details': response_data},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VerifyPaymentView(APIView):
    def get(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
            payment = Payment.objects.get(booking=booking)
            
            # Verify payment with Chapa
            verify_url = f"https://api.chapa.co/v1/transaction/verify/{payment.transaction_id}"
            headers = {
                "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"
            }
            
            response = requests.get(verify_url, headers=headers)
            response_data = response.json()

            if response.status_code == 200:
                # Update payment status
                if response_data['status'] == 'success':
                    payment.status = 'completed'
                else:
                    payment.status = 'failed'
                
                payment.chapa_response = response_data
                payment.save()

                # Send confirmation email if payment successful
                if payment.status == 'completed':
                    from .tasks import send_payment_confirmation_email
                    send_payment_confirmation_email.delay(booking.id)

                return Response(
                    PaymentSerializer(payment).data,
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Payment verification failed', 'details': response_data},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except (Booking.DoesNotExist, Payment.DoesNotExist):
            return Response(
                {'error': 'Booking or payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )