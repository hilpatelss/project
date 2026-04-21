from datetime import datetime, timedelta
from time import strftime
from django.contrib.auth.models import User
from datetime import date, timedelta
from django.shortcuts import render, redirect ,reverse
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect 
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate ,login ,logout
from django.contrib import messages
from myweb.models import *
from django.db.models import Sum

def home(request):
    # if user is already authenticated redirect to dashboard
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    context = {"page":"home"}
    return render(request,'index.html',context)

def about(request):
    # if user is already authenticated redirect to dashboard
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    context = {"page":"home"}
    return render(request,'about.html',context)

@login_required(login_url="/signin/")
def billing(request):
    # Generate new invoice 
    inv = Invoice.objects.filter(user = request.user).order_by('-id').first()
    inv_number = int(inv.Inv_number) + 1 if inv else 1
    today = date.today()
    due_date = today + timedelta(int(Formet.objects.filter(user = request.user).first().Inv_due_days))  # Example: due date is 30 days from today
    inv_format = Formet.objects.filter(user = request.user).first().Inv_prefix
    products = Products.objects.filter(user = request.user)
    data = {
        "inv_number": inv_number,
        "today":today ,
        "due_date":due_date,
        "inv_format": inv_format,
        "products": products
    }
    # Process invoice form submission
    if request.method == "POST":
        Customer_mobile = request.POST.get("Customer_number")
        Customer_name = request.POST.get("Customer_name")
        notes = request.POST.get("notes")
        Inv_bill_date = request.POST.get("Inv_bill_date")
        Inv_due_bill_date= request.POST.get("Inv_due_bill_date")
        Inv_payment_mode = request.POST.get("Inv_payment_mode")
        Product_name = request.POST.getlist("Product_name")
        Product_price = [int(x) for x in request.POST.getlist("Product_price")]
        Product_gst = [float(x) for x in request.POST.getlist("Product_gst")]
        Product_qty = [int(x) for x in request.POST.getlist("Product_qty")]
        Inv_subtotal = float(request.POST.get("Inv_subtotal", 0))
        Inv_gst = float(request.POST.get("Inv_gst", 0))
        Inv_Total = float(request.POST.get("Inv_Total", 0))
        Inv_additional_charges = float(request.POST.get("Inv_additional_charges", 0))
        Inv_discount = float(request.POST.get("Inv_discount", 0))
        if not Customer.objects.filter(user=request.user).filter(Customer_mobile = Customer_mobile).exists():
            # Create new customer
            customer = Customer.objects.create(
            user=request.user,
            Customer_name=Customer_name,
            Customer_mobile=Customer_mobile,
            customer_bill_count=1,
            customer_bill_spent=Inv_Total
            )
            customer.save()
        else:
            # Update existing customer's name if different
            customer = Customer.objects.filter(user=request.user).filter(Customer_mobile = Customer_mobile).first()
            if customer.Customer_name != Customer_name:
                customer.Customer_name = Customer_name
                customer.customer_bill_count += 1
                customer.customer_bill_spent += Inv_Total
                customer.save()
            else:
                customer.customer_bill_count += 1
                customer.customer_bill_spent += Inv_Total
                customer.save()
        invoice = Invoice.objects.create(
            user = request.user,
            Inv_number = inv_number,
            Inv_Total = Inv_Total,
            Inv_subtotal = Inv_subtotal,
            Inv_gst = Inv_gst,
            Inv_discount = Inv_discount,
            Inv_additional_charges = Inv_additional_charges,
            Inv_internal_notes = notes,
            Inv_bill_date = date.strptime(Inv_bill_date, '%Y-%m-%d'),
            Inv_due_bill_date = date.strptime(Inv_due_bill_date, '%Y-%m-%d'),
            Inv_payment_mode = Inv_payment_mode,
            Customer_number = Customer_mobile
        )
        invoice.save()        
        if len(Product_name) > 0:
            for i in range(len(Product_name)):
                if i < len(Product_price) and i < len(Product_gst) and i < len(Product_qty):
                    sell = Sells.objects.create(
                        user = request.user,
                        Inv_number = Invoice.objects.filter(user = request.user).filter(Inv_number = inv_number).first(),
                        Product_name = Product_name[i],
                        Product_qty = Product_qty[i],
                        Product_price = Product_price[i],
                        Product_gst = Product_gst[i]
                    )
                    sell.save()
                    products = Products.objects.filter(user = request.user).filter(Product_name = Product_name[i]).first()
                    if products:
                        products.Product_stock -= Product_qty[i]
                        products.save()
        inv_id = Invoice.objects.filter(user = request.user).filter(Inv_number = inv_number).first().id
        return redirect('invoice', inv_id= inv_id)
    context = {"page":"home", "data": data}
    return render(request,'billing.html',context)

@csrf_protect
@login_required(login_url="/signin/")   
def getcustomer(request):
    # Get customer name by mobile number for auto-fill in billing form
    if request.method == "POST":
        Customer_mobile = request.POST.get("Customer_mobile")     
        customer_name = Customer.objects.filter(user=request.user).filter(Customer_mobile = Customer_mobile).first().Customer_name
        if customer_name:   
            success = customer_name.title() 
        else:
            success = "Customer not found"
        return HttpResponse(success)

@login_required(login_url="/signin/")
def dashboard(request):
    # Generate dashboard data and statistics
    initials = request.user.first_name[0].upper() + request.user.last_name[0].upper() if request.user.first_name and request.user.last_name else "U"
    inv = Invoice.objects.filter(user = request.user)
    today_sales = inv.filter(Inv_bill_date = date.today()).aggregate(total=Sum('Inv_Total'))['total'] or 0
    monthly_sales = inv.filter(Inv_bill_date__year=date.today().year, Inv_bill_date__month=date.today().month).aggregate(total=Sum('Inv_Total'))['total'] or 0
    total_customers = Customer.objects.filter(user=request.user).count()
    total_products = Products.objects.filter(user=request.user).count()
    week = {}
    Seles_t = 0
    for i in range(6, -1, -1):
        day_date = date.today() - timedelta(days=i)
        day_name = day_date.strftime("%a")
        week[f"day_{6-i}"] = day_name
        sales = inv.filter(Inv_bill_date=day_date).aggregate(total=Sum('Inv_Total'))['total'] or 0
        Seles_t += sales     
    for i in range(7):
        day_sales = inv.filter(Inv_bill_date=date.today() - timedelta(days=6-i)).aggregate(total=Sum('Inv_Total'))['total'] or 0
        week[f"sales_per_{i}"] = (day_sales / Seles_t * 90) if Seles_t != 0 else 0
    recent_invoices = inv.order_by('-id')[:5]
    for inv in recent_invoices:   
        inv.Customer_name = Customer.objects.filter(user=request.user).filter(Customer_mobile = inv.Customer_number).first().Customer_name if Customer.objects.filter(user=request.user).filter(Customer_mobile = inv.Customer_number).exists() else " Unknown"
        inv.Inv_items = Sells.objects.filter(user=request.user).filter(Inv_number = inv).count()
        inv.Inv_status = "Paid" if inv.Inv_due_bill_date <= date.today() else "Pending" 
        inv.format = Formet.objects.filter(user = request.user).first().Inv_prefix  
    data = {
        "initials": initials,
        "today_sales": today_sales,
        "monthly_sales": monthly_sales,
        "total_customers": total_customers,
        "total_products": total_products,   
        "week": week,
        "recent_invoices": recent_invoices      
    }
    context = {"page":"home", "data": data}
    return render(request,'dashboard.html',context)

@login_required(login_url="/signin/")   
def customers(request):
    # Generate customer list and statistics for dashboard
    user = request.user   
    Cust  = Customer.objects.filter(user=user).order_by('-id')
    cust_new_this_week =0
    for c in Cust:
        if c.id >= Customer.objects.filter(user=user).filter(Customer_mobile = c.Customer_mobile).first().id and c.id >= Customer.objects.filter(user=user).filter(Customer_mobile = c.Customer_mobile).first().id - 5:
            cust_new_this_week += 1
    cust_total = Cust.count()
    T_revenue = 0
    Inv = Invoice.objects.filter(user = request.user)
    for i in Inv:
        T_revenue += i.Inv_Total
    for c in Cust:
        c.Customer_name = c.Customer_name.title()
        c.initials = c.Customer_name[0].upper() + c.Customer_name.split(" ")[-1][0].upper()
    Stats = {
        "cust_total": cust_total,
        "T_revenue": T_revenue,
        "cust_bills": Inv.count(),
        "cust_new_this_week": cust_new_this_week
    }
    context = {"page":"customers", "cust" : Cust , "Stats":Stats }
    return render(request,'customers.html',context)

@csrf_protect
@login_required(login_url="/signin/")   
def editcustomer(request):
    # Edit customer details from customer list page
    if request.method == "POST":
        Customer_name = request.POST.get("Customer_name")
        Customer_mobile = request.POST.get("Customer_mobile")
        Customer_email = request.POST.get("Customer_email")
        user = request.user
        cust  = Customer.objects.filter(user=user).filter(Customer_mobile = Customer_mobile).first()
        cust.Customer_name = Customer_name
        cust.Customer_mobile = Customer_mobile  
        cust.Customer_email = Customer_email
        cust.save()    
        return redirect('/customers/')
        
@csrf_protect
@login_required(login_url="/signin/")   
def addcustomer(request):
    # Add new customer from customer list page
    if request.method == "POST":
        user =request.user
        Customer_name = request.POST.get("Customer_name")
        Customer_mobile = request.POST.get("Customer_mobile")
        Customer_email = request.POST.get('Customer_email')
        cust = Customer.objects.create(
            user=user,
            Customer_name=Customer_name,
            Customer_mobile=Customer_mobile,
            Customer_email=Customer_email
        )
        cust.save()
        return redirect('/customers/')
    
@login_required(login_url="/signin/")   
def deletecustomer(request):
    # Delete customer from customer list page
    if request.method == "POST":
        User = request.user
        Customer_id = request.POST.get("Customer_id")

        cust = Customer.objects.filter(user=User).filter(id = Customer_id).first()
        if cust:
            cust.delete()

        return redirect('/customers/')
    return redirect('/customers/')
 
@login_required(login_url="/signin/")
def invoice(request, inv_id):
    # Generate invoice details for invoice view page
    user = request.user
    inv = Invoice.objects.filter(user = request.user).filter(id = inv_id).first()  
    formet = Formet.objects.filter(user = user).first()
    business = Business.objects.filter(user = user).first()
    customer = Customer.objects.filter(user=user).filter(Customer_mobile = inv.Customer_number).first()
    sells = Sells.objects.filter(user=user).filter(Inv_number = inv)
    for item in sells:
        item.Total = item.Product_price * item.Product_qty * (1 + (item.Product_gst ) / 100) if item.Product_gst != 0 else item.Product_price * item.Product_qty
    data = {
        "Shop_name": business.bizName if business else "",
        "Shop_address": business.full_address if business else "",
        "Shop_tagline" : "Your trusted local shop",
        "Shop_phone": business.phone_number if business else "",
        "Shop_Gstin": business.Gstin if business else "",
        "Inv_format": formet.Inv_prefix if formet else "",
        "Inv_number": inv.Inv_number,
        "Inv_status": "Paid" if inv.Inv_due_bill_date <= date.today() else "Pending",
        "Inv_date": inv.Inv_bill_date,
        "Inv_due_date": inv.Inv_due_bill_date,
        "Inv_payment_method": inv.Inv_payment_mode,
        "Inv_payment_status": inv.Inv_due_bill_date <= date.today() and "Paid" or "Pending",
        "Inv_subtotal": inv.Inv_subtotal,
        "Inv_gst": inv.Inv_gst,
        "Inv_discount": inv.Inv_discount,
        "Inv_total": inv.Inv_Total,
        "Customer_name": customer.Customer_name if customer else "",
        "Customer_mobile": customer.Customer_mobile if customer else "",
        "Customer_email": customer.Customer_email if customer else "",
        "sells": sells
    }
    context = {"page":"home", "data": data}
    return render(request,'invoice.html',context)


@login_required(login_url="/signin/")
def products(request):
    # Generate product list and stock status for products page
    User = request.user
    prod = Products.objects.filter(user=User)
    prod_count = prod.count()
    Prod_inStock = 0
    Prod_outStock = 0
    prod_lowStock = 0
    for p in prod:
        p.Product_name = p.Product_name.title()
        if p.Product_stock <= 0:
            p.Product_status = "out-stock"
            p.Product_design = "badge-out"
            Prod_outStock += 1
        elif p.Product_stock < 100:
            p.Product_status = "low-stock"
            p.Product_design = "badge-low"
            prod_lowStock += 1
        else:
            p.Product_status = "in-stock"
            p.Product_design = "badge-in"
            Prod_inStock += 1
    Stats = {
        "prod_count": prod_count,
        "Prod_inStock": Prod_inStock,
        "Prod_outStock": Prod_outStock,
        "prod_lowStock": prod_lowStock
    }
    context = {"page":"home", "prod": prod, "Stats": Stats}
    return render(request,'products.html',context)

@login_required(login_url="/signin/")   
def editproducts(request):
    # Edit product details from products page
    if request.method == "POST":
        id = request.POST.get("id")
        Name = request.POST.get("Name")
        Price = request.POST.get("Price")
        gst = request.POST.get('gst')
        Stock = request.POST.get('Stock')
        prod = Products.objects.filter(user=request.user).filter(id = id).first()
        prod.Product_name = Name
        prod.Product_price = Price
        prod.Product_gst = gst
        prod.Product_stock = Stock
        prod.save()
        return redirect('/products/')
    
@csrf_protect
@login_required(login_url="/signin/")   
def addproducts(request):
    # Add new product from products page
    if request.method == "POST":
        Name = request.POST.get("Name")
        Price = request.POST.get("Price")
        gst = request.POST.get('gst')
        Stock = request.POST.get('Stock')
        prod = Products.objects.create(
            user = request.user,
            Product_name = Name,
            Product_price = Price,
            Product_stock = Stock,
            Product_gst =gst
        )
        prod.save()
        return redirect('/products/')
    
@login_required(login_url="/signin/")   
def deleteproducts(request):
    # Delete product from products page
    if request.method == "POST":
        Products_id = request.POST.get("Products_id")
        User = request.user
        prod = Products.objects.filter(user=User).filter(id = Products_id).first()
        if prod:
            prod.delete()
        return redirect('/products/')
    return redirect('/products/')

@login_required(login_url="/signin/")
def reports(request):
    # Generate sales reports and analytics for reports page
    Inv = Invoice.objects.filter(user = request.user)
    total_revenue = 0
    total_gst =0
    for i in Inv:
        total_revenue = i.Inv_Total
        total_gst = i.Inv_gst
    total_invoices = Inv.count()
    avg_order_value = total_revenue/total_invoices if total_invoices != 0 else 0
    m = {}
    total_rev_c = 0
    for i in range(6, -1, -1):
        month_date = date.today() - timedelta(days=30*i)
        month_name = month_date.strftime("%b %Y")
        m[f"month_{7-i}"] = month_name
        month_revenue = Inv.filter(Inv_bill_date__year=month_date.year, Inv_bill_date__month=month_date.month).aggregate(total=Sum('Inv_Total'))['total'] or 0
        m[f"month_val_{7-i}"] = month_revenue
        total_rev_c += month_revenue
    for i in range(1, 8):
        month_val = m.get(f"month_val_{i}", 0)
        m[f"month_val_px_{i}"] = (month_val / total_rev_c * 130) if total_rev_c != 0 else 0
    p = {}
    sells = Sells.objects.filter(user = request.user)
    for s in sells:
        if s.Product_name in p:
            p[s.Product_name] += s.Product_price * s.Product_qty * (1 + (s.Product_gst ) / 100) if s.Product_gst != 0 else s.Product_price * s.Product_qty
        else:
            p[s.Product_name] = s.Product_price * s.Product_qty * (1 + (s.Product_gst ) / 100) if s.Product_gst != 0 else s.Product_price * s.Product_qty
    p = dict(sorted(p.items(), key=lambda item: item[1], reverse=True))
    p_t = {}
    total_p_t = sum(p.values())
    for i in range(1, 6):
        try:
            top_product = list(p.items())[i-1]
            p_t[f"top_product_{i}_name"] = top_product[0]
            p_t[f"top_product_{i}_revenue"] = top_product[1]
            p_t[f"top_product_{i}_per"] = (top_product[1] / total_p_t * 100) if total_p_t != 0 else 0
        except IndexError:
            p_t[f"top_product_{i}_name"] = "N/A"
            p_t[f"top_product_{i}_revenue"] = 0 
            p_t[f"top_product_{i}_per"] = 0
    month_summary = []
    for i in range(11, -1, -1):
        month_date = date.today() - timedelta(days=30*i)
        month_name = month_date.strftime("%b %Y")        
        invoice_count = Inv.filter(Inv_bill_date__year=month_date.year, Inv_bill_date__month=month_date.month).count()
        gross_sales = Inv.filter(Inv_bill_date__year=month_date.year, Inv_bill_date__month=month_date.month).aggregate(total=Sum('Inv_Total'))['total'] or 0
        gst_collected= Inv.filter(Inv_bill_date__year=month_date.year, Inv_bill_date__month=month_date.month).aggregate(total=Sum('Inv_gst'))['total'] or 0
        discounts= Inv.filter(Inv_bill_date__year=month_date.year, Inv_bill_date__month=month_date.month).aggregate(total=Sum('Inv_discount'))['total'] or 0
        net_revenue= gross_sales - discounts
        Growth = ((net_revenue - month_summary[-1]['net_revenue']) / month_summary[-1]['net_revenue'] * 100) if len(month_summary) > 0 and month_summary[-1]['net_revenue'] != 0 else 0     
        month_summary.append({
            "month_name": month_name,
            "invoice_count": invoice_count,
            "gross_sales":gross_sales,
            "gst_collected":gst_collected,
            "discounts":discounts,
            "net_revenue":net_revenue,
            "Growth":Growth
        }) 
    data= {
        "total_revenue": total_revenue,
        "total_invoices":total_invoices,
        "total_gst":total_gst,
        "avg_order_value":avg_order_value,
        "m": m,
        "p": p_t,
        "monthly_summary": list(reversed(month_summary))
    }
    context = {"page":"home", "data": data }
    return render(request,'reports.html',context)

@login_required(login_url="/signin/")
def sales_history(request):
    # Generate sales history and invoice list for sales history page
    user = request.user
    inv = Invoice.objects.filter(user =user)
    total_coll = 0
    total_pen = 0
    for i in inv:
        if i.Inv_due_bill_date > date.today():
            total_pen += i.Inv_Total
        else:
            total_coll += i.Inv_Total
            
    total_T_rev = inv.filter(Inv_due_bill_date__gte = date.today()).aggregate(total=Sum('Inv_Total'))['total'] or 0
    invoice = inv.order_by('-Inv_number')
    formet = Formet.objects.filter(user = user).first()
    for i in invoice: 
        i.Inv_items = Sells.objects.filter(user=user).filter(Inv_number = i).count()   
        i.Inv_status = "Paid" if i.Inv_due_bill_date <= date.today() else "Pending"
        if  Customer.objects.filter(user=user).filter(Customer_mobile = i.Customer_number).exists():
            i.Customer_name = Customer.objects.filter(user=user).filter(Customer_mobile = i.Customer_number).first().Customer_name 
        else :
            i.Customer_name = "Unknown"
        inv.Inv_items = Sells.objects.filter(user=user).filter(Inv_number = i).count()
    data = {
        "inv" : invoice,
        "total_inv": inv.count(),
        "total_coll": total_coll,
        "total_pen": total_pen,
        "total_T_rev": total_T_rev,
        "Formet": formet
    }
    context = {"page":"home","data": data}
    return render(request,'sales_history.html',context)

@csrf_protect
@login_required(login_url="/signin/")
def invoice_h(request):
    # Redirect to invoice view page when invoice number is searched from sales history page
    if request.method == "POST":
        inv_number = request.POST.get("inv_number")
        inv = Invoice.objects.filter(user = request.user).filter(Inv_number = inv_number).first()
        if inv:
            return redirect('invoice', inv_id= inv.id)
    return redirect('/sales_history/')

@login_required(login_url="/signin/")
def settings(request): 
    # Generate business and invoice format details for settings page
    user = request.user
    biz = Business.objects.filter(user = user).first()
    format = Formet.objects.filter(user = user).first()
    context = {"page":"home", "biz": biz, "user": user ,"format":format }
    return render(request,'settings.html',context)

@csrf_protect
@login_required(login_url="/signin/")
def editbiz(request):
    # edit business details
    if request.method == "POST":
        bizName = request.POST.get("bizName")
        full_name = request.POST.get("full_name")
        phone_number = request.POST.get("phone_number")
        full_address = request.POST.get("full_address")
        Gstin = request.POST.get("Gstin")
        Pan_number = request.POST.get("Pan_number")
        user = request.user
        business = Business.objects.filter(user=user).first()
        business.bizName = bizName
        business.full_address = full_address
        business.phone_number = phone_number
        business.Gstin = Gstin
        business.Pan_number = Pan_number if Pan_number else "N/A"
        business.save()
    return redirect('/settings/#tab-shop')

@csrf_protect
@login_required(login_url="/signin/")
def editinv(request):
    # edit invoice format and settings
    if request.method == "POST":
        Inv_prefix = request.POST.get("Inv_prefix")
        Inv_footer = request.POST.get("Inv_footer")
        Inv_due_days = request.POST.get("Inv_due_days")
        Show_signature_area = request.POST.get("Show_signature_area")
        Show_TC = request.POST.get("Show_TC")
        user = request.user
        format = Formet.objects.filter(user=user).first()
        format.Inv_prefix = Inv_prefix
        format.Inv_footer = Inv_footer
        format.Inv_due_days = Inv_due_days
        format.Show_signature_area = True if Show_signature_area == "true" else False
        format.Show_TC = True if Show_TC == "true" else False
        format.save()       
        return redirect(reverse('settings') + '#tab-invoice')

@csrf_protect
@login_required(login_url="/signin/")   
def edituser(request):
    # edit user account details and password 
    if request.method == "POST":
        username = request.POST.get("username")
        full_name = request.POST.get("full_name")
        first_name, last_name = full_name.split()
        pass1 = request.POST.get("pass1")
        pass2 = request.POST.get("pass2")
        if pass2 == "":
            user = request.user
            user.username = username
            user.first_name =first_name
            user.last_name =last_name
            user.save()
        else:
            user = request.user
            user.username = username
            user.first_name =first_name
            user.last_name =last_name
            if user == authenticate(username =username,password =pass1):
                user.set_password(pass2)
            user.save()
            return render('/settings/#tab-account')
        
        return render('/settings/#tab-account')
 
@csrf_protect
def signin(request):
    # Process user authentication and login
    if request.method =="POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        if not User.objects.filter(username = username).exists():
            messages.info(request, 'invalid Username')
            return redirect('/signin/')        
        user = authenticate(username =username,password =password)       
        if user is None:
            messages.info(request, 'invalid password')
            return redirect('/signin/')
        else:
            login(request ,user)
            return redirect('/dashboard/')
    context = {"page":"SignIn"}
    return render(request,'signin.html',context)

@csrf_protect
def signup(request):
    # Process user registration and create associated business and invoice format records
    if request.method == 'POST':
        first_name = request.POST.get("first_name") 
        last_name = request.POST.get("last_name") 
        username = request.POST.get("username")
        password = request.POST.get("password")
        phone_number = request.POST.get("phone_number")
        bizName = request.POST.get("bizName")
        bizType = request.POST.get("bizType")
        Gstin = request.POST.get("Gstin")
        City = request.POST.get("City")

        user= User.objects.filter(username = username)
        if  user.exists() :
            messages.info(request, 'username is alraedy register')
            return render(request,'signup.html',context)
        
        user = User.objects.create(
            first_name = first_name,
            last_name = last_name,
            username = username
        )
        user.set_password(password)
        user.save()
         
        if len(Gstin) == 0:
            Gstin ="A" 

        business = Business.objects.create(
            user =user, 
            phone_number = phone_number,
            bizName = bizName,
            bizType = bizType,
            Gstin = Gstin,
            City = City
        )
        business.save()

        formet = Formet.objects.create(
            user =user, 
        )
        formet.save()

        login(request ,user)
        return redirect('/dashboard/')
    context = {"page":"SignUp"}
    return render(request,'signup.html',context)

@login_required(login_url="/signin/")
def Signout(request):
    # User logout and redirect to sign-in page
    logout(request)
    return redirect('/signin/')


