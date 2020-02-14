from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from rango.models import Category, Page
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from datetime import datetime

# A helper method
def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val


# Updated the function definition
def visitor_cookie_handler(request):
    visits = int(get_server_side_cookie(request, 'visits', '1'))
    last_visit_cookie = get_server_side_cookie(request,
                                               'last_visit',
                                               str(datetime.now()))
    last_visit_time = datetime.strptime(last_visit_cookie[:-7],
                                        '%Y-%m-%d %H:%M:%S')
    # If it's been more than a day since the last visit...
    if (datetime.now() - last_visit_time).days > 0:
        visits = visits + 1
        # Update the last visit cookie now that we have updated the count
        request.session['last_visit'] = str(datetime.now())
    else:
        # Set the last visit cookie
        request.session['last_visit'] = last_visit_cookie
    # Update/set the visits cookie
    request.session['visits'] = visits



def index(request):
    # Query the database for a list of ALL categories currently stored.
    # Order the categories by the number of likes in descending order.
    # Retrieve the top 5 only -- or all if less than 5.
    # Place the list in our context_dict dictionary (with our boldmessage!)
    # that will be passed to the template engine.

    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('-views')[:5]

    context_dict = {}
    context_dict = {'boldmessage': 'Crunchy, creamy, cookie, candy, cupcake!'}
    context_dict['categories'] = category_list
    context_dict['pages'] = page_list

    visitor_cookie_handler(request)

    return render(request, 'rango/index.html', context=context_dict)


    
def about(request):
    context_dict = {'boldmessage': 'This tutorial has been put together by Ruofan Guo.'}

    visitor_cookie_handler(request)
    context_dict['visits'] = request.session['visits']
    return render(request, 'rango/about.html',context=context_dict)

def show_category(request, category_name_slug):
    # deal with requested passed 'category_name_slug'
    context_dict = {}

    try:
        #if find a category name slug with given varaible

        #.get() returns 1 category model instance
        category = Category.objects.get(slug=category_name_slug)
        #return related pages, attribute of page is the one in url

        pages = Page.objects.filter(category=category)

        #add the results ready to be render into templates context
        context_dict['pages'] = pages
        context_dict['category'] = category
    except Category.DoesNotExist:
        # cannot find , .get() raise DoesNotExist exception.
        #display nothing

        context_dict['pages'] = None      
        context_dict['category'] = None
    
    #render the response and return it to the client
    return render(request, 'rango/category.html', context=context_dict)

@login_required
def add_category(request):
    form = CategoryForm()
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save(commit=True)
            # return redirect('/rango/')
            return redirect(reverse('rango:index'))
        else:
            print(form.errors)
    return render(request, 'rango/add_category.html', {'form':form})

@login_required
def add_page(request, category_name_slug):
    try:
        category = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        category = None

    #cannot find the specific Category
    if category is None:
        # return redirect('/rango/')
        return redirect(reverse('rango:index'))
    #initialise the form
    form = PageForm()

    if request.method == "POST":
        form = PageForm(request.POST)
    
        if form.is_valid():
            if category:
                page = form.save(commit=False)
                page.category = category
                page.views = 0
                page.save()

                return redirect(reverse('rango:show_category', kwargs={'category_name_slug':category_name_slug}))
        else:
            print(form.errors)
    
    context_dict = {'form':form, 'category': category}
    return render(request, 'rango/add_page.html', context = context_dict)

def register(request):
    #a boolean value for telling the template
    # whether the registration is successful
    # initially  false, when succeeds true.
    registered = False

    # POST, handle the form data
    if request.method == "POST":
        # try to grab information from the raw form information
        # note that, we use both UserForm & UserProFileForm(additional attributes)
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST)

        # check whether the form data is valid
        if user_form.is_valid() and profile_form.is_valid():
            # save the UserForm data into database
            user = user_form.save()

            # Note that using the hasher to set password
            # And update the user instance
            user.set_password(user.password)
            user.save()

            # handle the UserProfile instance
            # we need to set the user attribute ourselves(self-defined)
            #we set commit = False, to <delay> the save(iniitially no user instance)
            profile = profile_form.save(commit=False)
            profile.user = user

            # if user provide the icon
            # get it from the input form then put it into UserProfile mdoel
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']
            
            #save the UserProfile(Form to database) model instance
            profile.save()

            # tells the teplates, registration finished
            registered = True
        else:
            # invalid forms data
            # print problems to the terminal
            print(user_form.errors, profile_form.errors)
    else:
        # not HTTP POST(maybe get HttpRequest)
        # so provide&tender the blank form for user
        user_form = UserForm()
        profile_form = UserProfileForm()

    # Render the template
    return render(request,'rango/register.html',context={'user_form':user_form,
    'profile_form':profile_form,'registered':registered})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # check whether the combination is valid
        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request,user)
                return redirect(reverse('rango:index'))
            else:
                # inactive account was used
                return HttpResponse("Your Rango account is disabled.")
        else:
            # bad login details ,cannot log the user in
            print(f"Invalid login details: {username}, {password}")
            return HttpResponse("Invalid login details supplied.")
    else:
        #HTTP GET
        return render(request,'rango/login.html')


@login_required
def restricted(request):
    return render(request, 'rango/restricted.html')

@login_required
def user_logout(request):
    logout(request)
    return redirect(reverse('rango:index'))