from django.shortcuts import render

# Create your views here.
def get_services(request):
    return render(request, 'index.html')