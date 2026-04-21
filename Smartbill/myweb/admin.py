from django.contrib import admin
from . import models
# Register your models here.



class Business(admin.ModelAdmin):
    list_display = ("user","id","bizType","phone_number","Gstin","City","full_address","Pan_number","Gst_enable","default_gst")
admin.site.register(models.Business, Business)

class Formet(admin.ModelAdmin):
    list_display = ("user","id","Inv_prefix","Inv_footer","Inv_due_days","Show_signature_area","Show_TC")
admin.site.register(models.Formet, Formet)

class Customer(admin.ModelAdmin):
    list_display= ("user","id","Customer_name", "Customer_mobile", "Customer_email", "customer_bill_count","customer_bill_spent")
admin.site.register(models.Customer, Customer)

class Products(admin.ModelAdmin):
    list_display =("user","id","Product_name","Product_price","Product_stock","Product_gst")
admin.site.register(models.Products, Products)

class Invoice(admin.ModelAdmin):
    list_display = ("user","id","Inv_number","Inv_Total","Inv_subtotal","Inv_gst","Inv_discount","Inv_additional_charges","Inv_internal_notes","Inv_bill_date","Inv_due_bill_date","Inv_payment_mode","Customer_number")
admin.site.register(models.Invoice,Invoice)

class Sells(admin.ModelAdmin):
    list_display = ("user","id","Inv_number","Product_name","Product_qty")
admin.site.register(models.Sells,Sells)

