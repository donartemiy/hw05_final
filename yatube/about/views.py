# from django.shortcuts import render
from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    """TemplateView - спец шаблон для статичных страниц.
    По умлочанию принимает только get. template_name - обязательная
    переменная. Идет из коробки, в ней расположение шалона"""
    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    template_name = 'about/tech.html'
