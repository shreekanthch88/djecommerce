import random
import string

import razorpay
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from zoneinfo import ZoneInfo
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, View
from django.db.models import Q

from .forms import CheckoutForm, CouponForm, RefundForm, ProfileForm, AddressBookForm
from .models import Item, OrderItem, Order, Address, Payment, Coupon, Refund, UserProfile, AddressBook, Wishlist


def welcome_page(request):
    return render(request, "welcome.html")


def get_razorpay_client():
    key_id = getattr(settings, "RAZORPAY_KEY_ID", "")
    key_secret = getattr(settings, "RAZORPAY_KEY_SECRET", "")
    if not key_id or not key_secret:
        return None
    return razorpay.Client(auth=(key_id, key_secret))


def razorpay_key_names():
    mode = getattr(settings, "RAZORPAY_MODE", "test")
    if mode == "live":
        return "RAZORPAY_LIVE_KEY_ID", "RAZORPAY_LIVE_KEY_SECRET"
    return "RAZORPAY_TEST_KEY_ID", "RAZORPAY_TEST_KEY_SECRET"


def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


def products(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request, "products.html", context)


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


def finalize_razorpay_order(request, order, razorpay_payment_id, razorpay_order_id, razorpay_signature):
    payment = Payment()
    payment.razorpay_payment_id = razorpay_payment_id
    payment.razorpay_order_id = razorpay_order_id
    payment.razorpay_signature = razorpay_signature
    payment.user = request.user
    payment.amount = order.get_total()
    payment.save()

    order_items = order.items.all()
    order_items.update(ordered=True)
    for item in order_items:
        item.save()

    order.ordered = True
    order.payment = payment
    order.ref_code = create_ref_code()
    order.save()

    messages.success(request, "Your order was successful!")
    return redirect("core:order-success")


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            ist_now = timezone.now().astimezone(ZoneInfo("Asia/Kolkata"))
            context = {
                'form': form,
                'couponform': CouponForm(),
                'order': order,
                'DISPLAY_COUPON_FORM': True,
                'MIN_AVAILABILITY_DATE': ist_now.date().isoformat(),
            }

            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='S',
                default=True
            )
            if shipping_address_qs.exists():
                context.update(
                    {'default_shipping_address': shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='B',
                default=True
            )
            if billing_address_qs.exists():
                context.update(
                    {'default_billing_address': billing_address_qs[0]})
            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                availability_date = form.cleaned_data.get('availability_date')
                availability_time = form.cleaned_data.get('availability_time')

                ist_now = timezone.now().astimezone(ZoneInfo("Asia/Kolkata"))
                if availability_date and availability_date < ist_now.date():
                    messages.info(self.request, "Availability date cannot be in the past")
                    return redirect('core:checkout')

                order.availability_date = availability_date
                order.availability_time = availability_time
                order.save()

                use_default_shipping = form.cleaned_data.get(
                    'use_default_shipping')
                if use_default_shipping:
                    print("Using the defualt shipping address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default shipping address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new shipping address")
                    shipping_address1 = form.cleaned_data.get(
                        'shipping_address')
                    shipping_address2 = form.cleaned_data.get(
                        'shipping_address2')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                        shipping_latitude = form.cleaned_data.get('shipping_latitude')
                        shipping_longitude = form.cleaned_data.get('shipping_longitude')
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip=shipping_zip,
                            latitude=shipping_latitude,
                            longitude=shipping_longitude,
                            address_type='S'
                        )
                        shipping_address.save()

                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get(
                            'set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required shipping address fields")
                        return redirect('core:checkout')

                use_default_billing = form.cleaned_data.get(
                    'use_default_billing')
                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print("Using the defualt billing address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default billing address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new billing address")
                    billing_address1 = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        billing_latitude = form.cleaned_data.get('billing_latitude')
                        billing_longitude = form.cleaned_data.get('billing_longitude')
                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                            latitude=billing_latitude,
                            longitude=billing_longitude,
                            address_type='B'
                        )
                        billing_address.save()

                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get(
                            'set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required billing address fields")
                        return redirect('core:checkout')

                payment_option = form.cleaned_data.get('payment_option')

                if payment_option == 'R':
                    return redirect('core:payment', payment_option='razorpay')
                else:
                    messages.warning(
                        self.request, "Invalid payment option selected")
                    return redirect('core:checkout')
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("core:order-summary")


class PaymentView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        payment_option = self.kwargs.get('payment_option')
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("core:order-summary")
        if payment_option == 'razorpay':
            if not order.billing_address:
                messages.warning(
                    self.request, "You have not added a billing address")
                return redirect("core:checkout")

            key_id = getattr(settings, "RAZORPAY_KEY_ID", "")
            if not key_id.startswith("rzp_"):
                key_name, _ = razorpay_key_names()
                messages.warning(
                    self.request,
                    f"Invalid Razorpay key id. Update {key_name} in .env and restart server."
                )
                return redirect("core:checkout")

            amount = int(order.get_total() * 100)
            if amount <= 0:
                messages.warning(self.request, "Order amount must be greater than 0 for Razorpay payment.")
                return redirect("core:checkout")

            client = get_razorpay_client()
            if client is None:
                key_id_name, key_secret_name = razorpay_key_names()
                messages.warning(
                    self.request,
                    f"Razorpay keys are missing. Add {key_id_name} and {key_secret_name} in .env."
                )
                return redirect("core:checkout")
            try:
                razorpay_order = client.order.create({
                    "amount": amount,
                    "currency": "INR",
                    "payment_capture": 1,
                })
            except Exception:
                messages.warning(
                    self.request,
                    "Unable to initialize Razorpay checkout. Check your configured Razorpay keys and internet connection."
                )
                return redirect("core:checkout")

            profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
            context = {
                "order": order,
                "DISPLAY_COUPON_FORM": False,
                "RAZORPAY_KEY_ID": key_id,
                "RAZORPAY_ORDER_ID": razorpay_order["id"],
                "RAZORPAY_AMOUNT": amount,
                "RAZORPAY_CALLBACK_URL": self.request.build_absolute_uri(
                    reverse("core:razorpay-callback")
                ),
                "PREFILL_NAME": self.request.user.get_full_name() or self.request.user.username,
                "PREFILL_EMAIL": self.request.user.email or "",
                "PREFILL_CONTACT": profile.phone_number or "",
            }
            self.request.session["razorpay_order_id"] = razorpay_order["id"]
            return render(self.request, "payment_razorpay.html", context)

        messages.warning(self.request, "This payment method is no longer available.")
        return redirect("core:checkout")

    def post(self, *args, **kwargs):
        payment_option = self.kwargs.get('payment_option')
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("core:order-summary")
        if payment_option == 'razorpay':
            client = get_razorpay_client()
            if client is None:
                key_id_name, key_secret_name = razorpay_key_names()
                messages.warning(
                    self.request,
                    f"Razorpay keys are missing. Add {key_id_name} and {key_secret_name} in .env."
                )
                return redirect("/payment/razorpay/")
            razorpay_payment_id = self.request.POST.get("razorpay_payment_id")
            razorpay_order_id = self.request.POST.get("razorpay_order_id")
            razorpay_signature = self.request.POST.get("razorpay_signature")

            if not (razorpay_payment_id and razorpay_order_id and razorpay_signature):
                messages.warning(self.request, "Invalid Razorpay payment data.")
                return redirect("/payment/razorpay/")

            try:
                client.utility.verify_payment_signature({
                    "razorpay_payment_id": razorpay_payment_id,
                    "razorpay_order_id": razorpay_order_id,
                    "razorpay_signature": razorpay_signature,
                })
            except razorpay.errors.SignatureVerificationError:
                messages.warning(self.request, "Payment verification failed.")
                return redirect("/payment/razorpay/")

            return finalize_razorpay_order(
                self.request, order, razorpay_payment_id, razorpay_order_id, razorpay_signature
            )

        messages.warning(self.request, "This payment method is no longer available.")
        return redirect("core:checkout")


@csrf_exempt
@login_required
def razorpay_callback(request):
    if request.method not in ["POST", "GET"]:
        return redirect("core:payment", payment_option="razorpay")

    try:
        order = Order.objects.get(user=request.user, ordered=False)
    except ObjectDoesNotExist:
        messages.warning(request, "You do not have an active order")
        return redirect("core:order-summary")

    client = get_razorpay_client()
    if client is None:
        key_id_name, key_secret_name = razorpay_key_names()
        messages.warning(
            request,
            f"Razorpay keys are missing. Add {key_id_name} and {key_secret_name} in .env."
        )
        return redirect("core:checkout")

    data = request.POST if request.method == "POST" else request.GET
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_order_id = data.get("razorpay_order_id") or request.session.get("razorpay_order_id")
    razorpay_signature = data.get("razorpay_signature")

    if not (razorpay_payment_id and razorpay_order_id and razorpay_signature):
        # Fallback for browser/script flows where callback fields are not posted.
        # We query Razorpay for payments on the created order and accept captured/authorized status.
        if razorpay_order_id:
            try:
                payments_data = client.order.payments(razorpay_order_id)
                items = payments_data.get("items", [])
                successful_payment = next(
                    (item for item in items if item.get("status") in ["captured", "authorized"]),
                    None
                )
                if successful_payment:
                    razorpay_payment_id = successful_payment.get("id")
                    razorpay_order_id = successful_payment.get("order_id") or razorpay_order_id
                    razorpay_signature = razorpay_signature or ""
                    request.session.pop("razorpay_order_id", None)
                    return finalize_razorpay_order(
                        request, order, razorpay_payment_id, razorpay_order_id, razorpay_signature
                    )
            except Exception:
                pass
        messages.warning(request, "Invalid Razorpay payment data.")
        return redirect("core:payment", payment_option="razorpay")

    try:
        client.utility.verify_payment_signature({
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_order_id": razorpay_order_id,
            "razorpay_signature": razorpay_signature,
        })
    except razorpay.errors.SignatureVerificationError:
        messages.warning(request, "Payment verification failed.")
        return redirect("core:payment", payment_option="razorpay")

    request.session.pop("razorpay_order_id", None)
    return finalize_razorpay_order(
        request, order, razorpay_payment_id, razorpay_order_id, razorpay_signature
    )


class HomeView(ListView):
    model = Item
    paginate_by = 10
    template_name = "home.html"
    
    def get_queryset(self):
        category = self.request.GET.get('category')
        search = (self.request.GET.get('search') or '').strip()
        queryset = Item.objects.all().order_by('-id')

        if category:
            queryset = queryset.filter(category=category)

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(category__icontains=search)
            )

        return queryset


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("/")


class OrderSuccessView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        latest_order = Order.objects.filter(
            user=self.request.user, ordered=True
        ).order_by("-ordered_date").first()
        context = {
            "order": latest_order,
        }
        return render(self.request, "order_success.html", context)


class AccountView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        user = self.request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        form = ProfileForm(initial={
            "full_name": user.get_full_name(),
            "email": user.email,
            "phone_number": profile.phone_number,
            "date_of_birth": profile.date_of_birth,
        })
        addresses = AddressBook.objects.filter(user=user).order_by("-is_default", "-id")
        context = {
            "form": form,
            "profile": profile,
            "addresses": addresses,
        }
        return render(self.request, "account.html", context)

    def post(self, *args, **kwargs):
        user = self.request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        form = ProfileForm(self.request.POST, self.request.FILES)
        if form.is_valid():
            full_name = form.cleaned_data.get("full_name", "")
            email = form.cleaned_data.get("email", "")
            phone_number = form.cleaned_data.get("phone_number", "")
            date_of_birth = form.cleaned_data.get("date_of_birth")
            profile_picture = form.cleaned_data.get("profile_picture")

            if full_name:
                parts = full_name.split(" ", 1)
                user.first_name = parts[0]
                user.last_name = parts[1] if len(parts) > 1 else ""
            if email:
                user.email = email
            user.save()

            profile.phone_number = phone_number
            profile.date_of_birth = date_of_birth
            if profile_picture:
                profile.profile_picture = profile_picture
            profile.save()

            messages.success(self.request, "Profile updated successfully.")
            return redirect("core:account")

        context = {
            "form": form,
            "profile": profile,
            "addresses": AddressBook.objects.filter(user=user).order_by("-is_default", "-id"),
        }
        return render(self.request, "account.html", context)


class AddressBookCreateView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        form = AddressBookForm()
        return render(self.request, "account_address_form.html", {"form": form, "mode": "add"})

    def post(self, *args, **kwargs):
        form = AddressBookForm(self.request.POST)
        if form.is_valid():
            is_default = self.request.POST.get("is_default") == "on"
            if is_default:
                AddressBook.objects.filter(user=self.request.user, is_default=True).update(is_default=False)
            AddressBook.objects.create(
                user=self.request.user,
                full_name=form.cleaned_data["full_name"],
                phone_number=form.cleaned_data["phone_number"],
                house_no=form.cleaned_data["house_no"],
                street_area=form.cleaned_data["street_area"],
                city=form.cleaned_data["city"],
                state=form.cleaned_data["state"],
                pin_code=form.cleaned_data["pin_code"],
                country=form.cleaned_data["country"],
                is_default=is_default,
            )
            messages.success(self.request, "Address added successfully.")
            return redirect("core:account")
        return render(self.request, "account_address_form.html", {"form": form, "mode": "add"})


class AddressBookUpdateView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        address = get_object_or_404(AddressBook, pk=kwargs["pk"], user=self.request.user)
        form = AddressBookForm(initial={
            "full_name": address.full_name,
            "phone_number": address.phone_number,
            "house_no": address.house_no,
            "street_area": address.street_area,
            "city": address.city,
            "state": address.state,
            "pin_code": address.pin_code,
            "country": address.country,
        })
        return render(self.request, "account_address_form.html", {"form": form, "mode": "edit", "address": address})

    def post(self, *args, **kwargs):
        address = get_object_or_404(AddressBook, pk=kwargs["pk"], user=self.request.user)
        form = AddressBookForm(self.request.POST)
        if form.is_valid():
            is_default = self.request.POST.get("is_default") == "on"
            if is_default:
                AddressBook.objects.filter(user=self.request.user, is_default=True).update(is_default=False)
            address.full_name = form.cleaned_data["full_name"]
            address.phone_number = form.cleaned_data["phone_number"]
            address.house_no = form.cleaned_data["house_no"]
            address.street_area = form.cleaned_data["street_area"]
            address.city = form.cleaned_data["city"]
            address.state = form.cleaned_data["state"]
            address.pin_code = form.cleaned_data["pin_code"]
            address.country = form.cleaned_data["country"]
            address.is_default = is_default
            address.save()
            messages.success(self.request, "Address updated successfully.")
            return redirect("core:account")
        return render(self.request, "account_address_form.html", {"form": form, "mode": "edit", "address": address})


class AddressBookDeleteView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        address = get_object_or_404(AddressBook, pk=kwargs["pk"], user=self.request.user)
        return render(self.request, "account_address_confirm_delete.html", {"address": address})

    def post(self, *args, **kwargs):
        address = get_object_or_404(AddressBook, pk=kwargs["pk"], user=self.request.user)
        address.delete()
        messages.success(self.request, "Address deleted.")
        return redirect("core:account")


class AddressBookSetDefaultView(LoginRequiredMixin, View):
    def post(self, *args, **kwargs):
        address = get_object_or_404(AddressBook, pk=kwargs["pk"], user=self.request.user)
        AddressBook.objects.filter(user=self.request.user, is_default=True).update(is_default=False)
        address.is_default = True
        address.save()
        messages.success(self.request, "Default address set.")
        return redirect("core:account")


class OrderHistoryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        orders = Order.objects.filter(user=self.request.user, ordered=True).order_by("-ordered_date")
        return render(self.request, "order_history.html", {"orders": orders})


class OrderDetailView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        order = get_object_or_404(Order, pk=kwargs["pk"], user=self.request.user)
        return render(self.request, "order_detail.html", {"order": order})


class CancelOrderView(LoginRequiredMixin, View):
    def post(self, *args, **kwargs):
        order = get_object_or_404(Order, pk=kwargs["pk"], user=self.request.user)
        if order.status in ["DELIVERED", "CANCELLED"]:
            messages.warning(self.request, "Order cannot be cancelled.")
            return redirect("core:order-history")
        order.status = "CANCELLED"
        order.save()
        messages.success(self.request, "Order cancelled.")
        return redirect("core:order-history")


class WishlistView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        wishlist_items = Wishlist.objects.filter(user=self.request.user).select_related("item")
        return render(self.request, "wishlist.html", {"wishlist_items": wishlist_items})


@login_required
def add_to_wishlist(request, slug):
    item = get_object_or_404(Item, slug=slug)
    Wishlist.objects.get_or_create(user=request.user, item=item)
    messages.success(request, "Added to wishlist.")
    return redirect("core:wishlist")


@login_required
def remove_from_wishlist(request, slug):
    item = get_object_or_404(Item, slug=slug)
    Wishlist.objects.filter(user=request.user, item=item).delete()
    messages.success(request, "Removed from wishlist.")
    return redirect("core:wishlist")


@login_required
def move_wishlist_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    Wishlist.objects.filter(user=request.user, item=item).delete()
    return redirect("core:add-to-cart", slug=slug)


class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_item = self.object
        context['related_items'] = Item.objects.filter(
            category=current_item.category
        ).exclude(
            pk=current_item.pk
        ).order_by('-id')[:3]
        return context


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            return redirect("core:order-summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
        return redirect("core:order-summary")


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, "This item was removed from your cart.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)


def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("core:checkout")


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("core:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("core:checkout")


class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form
        }
        return render(self.request, "request_refund.html", context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            # edit the order
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                # store the refund
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, "Your request was received.")
                return redirect("core:request-refund")

            except ObjectDoesNotExist:
                messages.info(self.request, "This order does not exist.")
                return redirect("core:request-refund")
