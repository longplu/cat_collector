from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import Cat, Toy, Photo
from .forms import FeedingForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

import boto3
import uuid

S3_BASE_URL = 'https://s3.us-east-1.amazonaws.com/'
BUCKET = 'catcollector-llu'

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

@login_required
def cats_index(request):
    cats = Cat.objects.filter(user=request.user)
    return render(request, 'cats/index.html', {'cats': cats})

@login_required
def cats_detail(request, cat_id):
   cat = Cat.objects.get(id=cat_id)
   feeding_form = FeedingForm()
   toys_cat_doesnt_have = Toy.objects.exclude(id__in = cat.toys.all().values_list('id'))

   return render(request, 'cats/detail.html', {
       'cat': cat, 
       'feeding_form': feeding_form,
       'toys': toys_cat_doesnt_have,
    })

@login_required
def add_feeding(request, cat_id):
    # 1) collect form input values
    form = FeedingForm(request.POST)
    # 2) valid input values
    if form.is_valid():
        # 3) save a copy of a new feeding instance in memory
        new_feeding = form.save(commit=False)
        # 4) attach a reference to the cat that owns the feeding
        new_feeding.cat_id = cat_id
        # 5) save the new feeding to the database
        new_feeding.save()
    # 6) redirect the user back to the detail
    return redirect('detail', cat_id=cat_id)

# Renders a template with a form on it
# Creates a model form based on the model
# Responds to GET and POST requests
#  1) GET render the new cat form
#  2) POST submit the form to create a new instance
# Validate form inputs
# Handles the necessary redirect following a model instance creating

@login_required
def assoc_toy(request, cat_id, toy_id):
    Cat.objects.get(id=cat_id).toys.add(toy_id)
    return redirect('detail', cat_id=cat_id)

@login_required
def add_photo(request, cat_id):
    # attempt to collect the photo information from the form submission
    photo_file = request.FILES.get('photo-file')
    """
        <input type="file" name="photo-file"/> - this is what the get is referencing in html
    """
    # use an if statement to see if the photo information is present or not
    # if photo present
    if photo_file:
        # initialize a reference to the S3 service from boto3
        s3 = boto3.client('s3')
        # create a unique name for the photo asset
        key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
        """
            cute_kitten.png => h8sdkw.png - how a unique name is created for the uploaded file
        """
        # attempt to upload the photo asset to AWS S3
        try:
            s3.upload_fileobj(photo_file, BUCKET, key)
            # Save a secure url to the AWS S3 hosted photo asset to the database
            url = f"{S3_BASE_URL}{BUCKET}/{key}"

            photo = Photo(url=url, cat_id=cat_id)

            photo.save()
        # if upload is not succcessful
        except Exception as error:
            # print errors to the console
            print('***************************************')
            print('***************************************')
            print('An error occurred while uploading to S3')
            print(error)
            print('***************************************')
            print('***************************************')
        
        # return a response as a redirect to the client - redirect to the detail page
    return redirect('detail', cat_id=cat_id)

def signup(request):
    error_message = ''
    # check for POST request
    if request.method == 'POST':
        # capture form inputs
        form = UserCreationForm(request.POST)
        # validate form inputs
        if form.is_valid():
            # save the new user
            user = form.save()
            # log the new user in
            login(request, user)
            # redirect to cats index page
            return redirect('index')
        # if form is not valid
        else:
            error_message = 'invalid sign up - please try again'
            #redirect back to /accounts/signup and display error message
    # If GET request
    
        #render a signup page with a blank user creation form
    form = UserCreationForm()
    context = {'form':form, 'error':error_message}
    return render(request, 'registration/signup.html', context)


class CatCreate(LoginRequiredMixin, CreateView):
    model = Cat
    # fields = ('name', 'breed', 'age', 'description')
    fields = ('name', 'breed', 'description', 'age')
    # success_url = '/cats/' this will work, but it's not preferred
    # Fat Models, Skinny Controllers
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class CatUpdate(LoginRequiredMixin, UpdateView):
    model = Cat
    fields = ('name', 'breed', 'description', 'age')

class CatDelete(LoginRequiredMixin, DeleteView):
    model = Cat
    success_url = '/cats/'

class ToyCreate(LoginRequiredMixin, CreateView):
    model = Toy
    fields = ('name', 'color')


class ToyUpdate(LoginRequiredMixin, UpdateView):
    model = Toy
    fields = ('name', 'color')


class ToyDelete(LoginRequiredMixin, DeleteView):
    model = Toy
    success_url = '/toys/'


class ToyDetail(LoginRequiredMixin, DetailView):
    model = Toy
    template_name = 'toys/detail.html'


class ToyList(LoginRequiredMixin, ListView):
    model = Toy
    template_name = 'toys/index.html'