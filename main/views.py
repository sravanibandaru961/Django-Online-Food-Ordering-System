from django.shortcuts import render, get_object_or_404, redirect
from .models import Item, CartItems, Reviews
from django.contrib import messages
from .forms import DishRequestForm
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .decorators import *
from django.db.models import Sum, F, FloatField, ExpressionWrapper


# =========================
# HOME PAGE
# =========================

class MenuListView(ListView):
    model = Item
    template_name = 'main/home.html'
    context_object_name = 'menu_items'


# =========================
# FOOD DETAILS
# =========================

def menuDetail(request, slug):
    item = Item.objects.filter(slug=slug).first()
    reviews = Reviews.objects.filter(
        rslug=slug
    ).order_by('-id')[:7]

    context = {
        'item': item,
        'reviews': reviews,
    }

    return render(request, 'main/dishes.html', context)


# =========================
# ADD REVIEW
# =========================

@login_required
def add_reviews(request):

    if request.method == "POST":

        user = request.user
        rslug = request.POST.get("rslug")

        item = Item.objects.get(slug=rslug)

        review = request.POST.get("review")

        reviews = Reviews(
            user=user,
            item=item,
            review=review,
            rslug=rslug
        )

        reviews.save()

        messages.success(
            request,
            "Thankyou for reviewing this product!!"
        )

        return redirect("main:dishes", slug=item.slug)

    return redirect("main:home")


# =========================
# CREATE FOOD ITEM
# =========================

class ItemCreateView(LoginRequiredMixin, CreateView):

    model = Item

    fields = [
        'title',
        'image',
        'description',
        'price',
        'pieces',
        'instructions',
        'labels',
        'label_colour',
        'slug'
    ]

    def form_valid(self, form):

        form.instance.created_by = self.request.user

        return super().form_valid(form)


# =========================
# UPDATE FOOD ITEM
# =========================

class ItemUpdateView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    UpdateView
):

    model = Item

    fields = [
        'title',
        'image',
        'description',
        'price',
        'pieces',
        'instructions',
        'labels',
        'label_colour',
        'slug'
    ]

    def form_valid(self, form):

        form.instance.created_by = self.request.user

        return super().form_valid(form)

    def test_func(self):

        item = self.get_object()

        return self.request.user == item.created_by


# =========================
# DELETE FOOD ITEM
# =========================

class ItemDeleteView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DeleteView
):

    model = Item

    success_url = '/item_list'

    def test_func(self):

        item = self.get_object()

        return self.request.user == item.created_by


# =========================
# ADD TO CART
# =========================

@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)

    cart_item = CartItems.objects.create(
        user=request.user,
        item=item,
        ordered=False,
        quantity=1
    )

    messages.info(request, "Added to Cart!!")

    return redirect("main:cart")


# =========================
# CART PAGE
# =========================

@login_required
def get_cart_items(request):

    cart_items = CartItems.objects.filter(
        user=request.user,
        ordered=False
    )

    # Total price = item price × quantity
    total = cart_items.aggregate(
        total_price=Sum(
            ExpressionWrapper(
                F('item__price') * F('quantity'),
                output_field=FloatField()
            )
        )
    )['total_price']

    # Total number of items
    count = cart_items.aggregate(
        total_quantity=Sum('quantity')
    )['total_quantity']

    # Total pieces = pieces × quantity
    total_pieces = cart_items.aggregate(
        total_pieces=Sum(
            ExpressionWrapper(
                F('item__pieces') * F('quantity'),
                output_field=FloatField()
            )
        )
    )['total_pieces']

    # If cart is empty
    if total is None:
        total = 0

    if count is None:
        count = 0

    if total_pieces is None:
        total_pieces = 0

    context = {
        'cart_items': cart_items,
        'total': total,
        'count': count,
        'total_pieces': total_pieces
    }

    return render(
        request,
        'main/cart.html',
        context
    )


# =========================
# REMOVE ITEM FROM CART
# =========================

class CartDeleteView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DeleteView
):

    model = CartItems

    success_url = '/cart'

    def test_func(self):

        cart = self.get_object()

        return self.request.user == cart.user


# =========================
# INCREASE QUANTITY
# =========================

@login_required
def increase_quantity(request, pk):

    cart_item = get_object_or_404(
        CartItems,
        pk=pk,
        user=request.user,
        ordered=False
    )

    cart_item.quantity += 1

    cart_item.save()

    return redirect("main:cart")


# =========================
# DECREASE QUANTITY
# =========================

@login_required
def decrease_quantity(request, pk):

    cart_item = get_object_or_404(
        CartItems,
        pk=pk,
        user=request.user,
        ordered=False
    )

    if cart_item.quantity > 1:

        cart_item.quantity -= 1

        cart_item.save()

    else:

        cart_item.delete()

    return redirect("main:cart")


# =========================
# PLACE ORDER
# =========================

@login_required
def order_item(request):

    cart_items = CartItems.objects.filter(
        user=request.user,
        ordered=False
    )

    ordered_date = timezone.now()

    cart_items.update(
        ordered=True,
        ordered_date=ordered_date
    )

    messages.info(
        request,
        "Item Ordered"
    )

    return redirect("main:order_details")


# =========================
# ORDER DETAILS
# =========================

@login_required
def order_details(request):

    items = CartItems.objects.filter(
        user=request.user,
        ordered=True,
        status="Active"
    ).order_by('-ordered_date')

    cart_items = CartItems.objects.filter(
        user=request.user,
        ordered=True,
        status="Delivered"
    ).order_by('-ordered_date')

    # Active orders total
    total = items.aggregate(
        total_price=Sum(
            ExpressionWrapper(
                F('item__price') * F('quantity'),
                output_field=FloatField()
            )
        )
    )['total_price']

    count = items.aggregate(
        total_quantity=Sum('quantity')
    )['total_quantity']

    total_pieces = items.aggregate(
        total_pieces=Sum(
            ExpressionWrapper(
                F('item__pieces') * F('quantity'),
                output_field=FloatField()
            )
        )
    )['total_pieces']

    if total is None:
        total = 0

    if count is None:
        count = 0

    if total_pieces is None:
        total_pieces = 0

    context = {
        'items': items,
        'cart_items': cart_items,
        'total': total,
        'count': count,
        'total_pieces': total_pieces
    }

    return render(
        request,
        'main/order_details.html',
        context
    )


# =========================
# ADMIN VIEW
# =========================

@login_required(login_url='/accounts/login/')
@admin_required
def admin_view(request):

    cart_items = CartItems.objects.filter(
        item__created_by=request.user,
        ordered=True,
        status="Delivered"
    ).order_by('-ordered_date')

    context = {
        'cart_items': cart_items,
    }

    return render(
        request,
        'main/admin_view.html',
        context
    )


# =========================
# ITEM LIST
# =========================

@login_required(login_url='/accounts/login/')
@admin_required
def item_list(request):

    items = Item.objects.filter(
        created_by=request.user
    )

    context = {
        'items': items
    }

    return render(
        request,
        'main/item_list.html',
        context
    )


# =========================
# UPDATE ORDER STATUS
# =========================

@login_required
@admin_required
def update_status(request, pk):

    if request.method == 'POST':

        status = request.POST.get('status')

        cart_items = CartItems.objects.filter(
            item__created_by=request.user,
            ordered=True,
            status="Active",
            pk=pk
        )

        if status == 'Delivered':

            delivery_date = timezone.now()

            cart_items.update(
                status=status,
                delivery_date=delivery_date
            )

    return redirect("main:pending_orders")


# =========================
# PENDING ORDERS
# =========================

@login_required(login_url='/accounts/login/')
@admin_required
def pending_orders(request):

    items = CartItems.objects.filter(
        item__created_by=request.user,
        ordered=True,
        status="Active"
    ).order_by('-ordered_date')

    context = {
        'items': items,
    }

    return render(
        request,
        'main/pending_orders.html',
        context
    )


# =========================
# ADMIN DASHBOARD
# =========================

@login_required(login_url='/accounts/login/')
@admin_required
def admin_dashboard(request):

    cart_items = CartItems.objects.filter(
        item__created_by=request.user,
        ordered=True
    )

    pending_total = CartItems.objects.filter(
        item__created_by=request.user,
        ordered=True,
        status="Active"
    ).count()

    completed_total = CartItems.objects.filter(
        item__created_by=request.user,
        ordered=True,
        status="Delivered"
    ).count()

    # Total income
    income = cart_items.aggregate(
        total_income=Sum(
            ExpressionWrapper(
                F('item__price') * F('quantity'),
                output_field=FloatField()
            )
        )
    )['total_income']

    if income is None:
        income = 0

    context = {
        'pending_total': pending_total,
        'completed_total': completed_total,
        'income': income,
        'count1': 0,
        'count2': 0,
        'count3': 0,
    }

    return render(
        request,
        'main/admin_dashboard.html',
        context
    )

@login_required
def request_dish(request):

    if request.method == "POST":
        form = DishRequestForm(request.POST)

        if form.is_valid():
            dish_request = form.save(commit=False)
            dish_request.user = request.user
            dish_request.save()

            messages.success(
                request,
                "Your dish request has been submitted successfully!"
            )

            return redirect("main:home")

    else:
        form = DishRequestForm()

    return render(
        request,
        "main/request_dish.html",
        {"form": form}
    )