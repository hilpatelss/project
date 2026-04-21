from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('billing/', views.billing, name='billing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('invoice/<int:inv_id>/', views.invoice, name='invoice'),
    path('invoice_h/', views.invoice_h, name='invoice_h'),
    path('products/', views.products, name='products'),
    path('reports/', views.reports, name='reports'),
    path('settings/', views.settings, name='settings'),
    path('sales_history/', views.sales_history, name='sales_history'),
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('Signout/' , views.Signout , name="Signout"),
    path('customers/', views.customers, name='customers'),
    path('editbiz/', views.editbiz, name='editbiz'),
    path('settings/editbiz/', views.editbiz, name='editbiz'),
    path('editinv/', views.editinv, name='editinv'),
    path('edituser/', views.edituser, name='edituser'),
    path('editcustomer/', views.editcustomer, name='editcustomer'),
    path('addcustomer/', views.addcustomer, name='addcustomer'),
    path('deletecustomer/', views.deletecustomer, name='deletecustomer'),
    path('editproducts/', views.editproducts, name='editproducts'),
    path('addproducts/', views.addproducts, name='addproducts'),
    path('deleteproducts/', views.deleteproducts, name='deleteproducts'),
    path('getcustomer/', views.getcustomer, name='getcustomer'),
    
]