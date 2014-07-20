import os
import re
import sys
import datetime


#Settings
from django.conf import settings

from django.core.files import File
#Rendu
from django.shortcuts import render
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse, Http404

# from django.contrib.auth.forms import UserCreationForm
from django.utils.datastructures import MultiValueDictKeyError
from django.contrib.auth.decorators import login_required
from django.template import Context
from django.template import RequestContext

import hashlib

# Emails
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context


#search for creation
from search_engine.aws_req import compute_args
from .models import Book, UniqueBook, Recherche
#Usr_management models
from usr_management.models import UserKooblit, Syntheses

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from .forms import UploadFileForm

# Imaginary function to handle an uploaded file.
# from somewhere import handle_uploaded_file
from HTMLParser import HTMLParser

#!/usr/bin/env python
"""
This file opens a docx (Office 2007) file and dumps the text.

If you need to extract text from documents, use this file as a basis for your
work.

Part of Python's docx module - http://github.com/mikemaccana/python-docx
See LICENSE for licensing information.
"""

#fichier docx
from docx import opendocx, getdocumentHtml


def check_html(file_name):
    parser = HTMLParser()
    with open(file_name, 'rb') as _f:
        parser.feed(_f.read())

from pyPdf import PdfFileReader
from pyPdf.utils import PdfReadError
def check_pdf(file_name):
    try:
        doc = PdfFileReader(file(file_name, "rb"))
        return 0
    except PdfReadError, e:
        return 1
    except Exception:
        raise
# _file = models.FileField(upload_to="syntheses")
#     user = models.ForeignKey('UserKooblit')
#     livre_id = models.CharField(max_length=240, unique=True, default=False)
#     nb_achat = models.BigIntegerField(default=0)
#     note_moyenne = models.BigIntegerField(default=0)
#     nbre_notes = models.BigIntegerField(default=0)
#     date = models.DateField(null=True, default=datetime.datetime.now)
#     prix = models.DecimalField(max_digits=6, decimal_places=2)
def handle_uploaded_file(f, book_title, title, csrf_token, username):
    file_name = ''.join(('/tmp/', f.name, csrf_token))
    book = Book.objects.get(title=book_title)
    user = UserKooblit.objects.get(username=username)

    with open(file_name, 'wb') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    document = opendocx(file_name)
    with open(file_name+'.html', 'w') as newfile:
        # newfile = open(file_name+'.html', 'w')
        paratextlist = getdocumentHtml(document)
        # Make explicit unicode version
        newparatextlist = []
        for paratext in paratextlist:
            newparatextlist.append(paratext.encode("utf-8"))

        # Print out text of document with two newlines under each paragraph
        newfile.write('\n\n'.join(newparatextlist))    


    with open(file_name, 'rb') as destination:
        with open(file_name+'.html', 'r') as newfile:
            synthese = Syntheses(_file=File(destination), _file_html=File(newfile), 
                title=title, user=user, livre_id=book.id, prix=2)
            synthese.save()


def undo(s):
    s = s.split("%")
    tmp = []
    for i in s:
        if i:
            v = chr(int(i[:2],16))
            tmp.extend([v,i[2:]])
    return ''.join(tmp)

def create_book(book_title):
    s = compute_args(book_title, settings.AMAZON_KEY, exact_match=1, delete_duplicate=0)
    if not s:
        return 1
    first = s[0]
    b = Book(small_title=first['title'][:32], title=first['title'][:256], 
        author=[first['author']], description=first['summary'])
    b.save()
    r = Recherche(book=b, nb_searches=1)
    r.save()
    for book_dsc in s:
        try:
            u_b = UniqueBook(book=b, isbn=book_dsc['isbn'], image=book_dsc['image'])
            u_b.save()
        except Exception, e:
            pass
    return 0

def create_book_if_doesnt_exist(book_title):
    try:
        b = Book.objects.get(title=book_title)
    except Book.DoesNotExist, e:
        create_book(book_title)
    except Exception:
        raise

@login_required
def upload_file(request, book_title):
    if request.method == 'POST':
        # data = request.POST['data']
        # h = HTMLParser()
        # data = u''.join((data,))
        # with open('/tmp/test.html', 'w') as f:
        #     f.write(data)
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            if handle_uploaded_file(request.FILES['file'], request.GET['title'], request.POST['title'],
                request.POST['csrfmiddlewaretoken'], request.user.username):
                return render_to_response('upload.html', RequestContext(request))
        # return HttpResponseRedirect('/')
    else:
        form = UploadFileForm()
    return render_to_response('upload.html', RequestContext(request,{'form': form}))


def computeEmail(username, book_title):
    htmly = get_template('email_demande_infos.html')
    email = UserKooblit.objects.get(username=username).email
    d = Context({'username': username, 'book_title': book_title})
    subject, from_email, to = ('[Kooblit] Alerte pour '+book_title, 
                                'noreply@kooblit.com', email)
    html_content = htmly.render(d)
    msg = EmailMultiAlternatives(subject, html_content, from_email, [to])
    msg.content_subtype = "html"
    msg.send()

# def book_detail(request, book_title):
#     b = Book.objects(title=book_title)
#     if not b:
#         return render_to_response('doesnotexist.html',RequestContext(request))
#     else:
#         return render_to_response('details.html',RequestContext(request))

    # small_title = StringField(max_length=32, required=True, unique=True)
    # title = StringField(max_length=100, required=True, unique=True)
    # author = ListField(StringField(max_length=100, required=True))
    # description = StringField(max_length=4096, required=False)
    # genres = ListField(ReferenceField(Genre, reverse_delete_rule=NULLIFY))
    # nb_searches = ListField(LongField())
# class UniqueBook(Document):
#     """docstring for UniqueBook"""
#     book = ReferenceField(Book)
#     isbn = StringField(max_length=100, required=True, unique=True)
#     image = URLField()
#     last_update = DateTimeField(default=datetime.datetime.now)
# import pdb;pdb.set_trace()



@login_required
def book_search(request, book_title):
    if request.method == 'GET':
        a = 0
        try:
            refer = request.META['HTTP_REFERER']
            a = re.match("http://"+request.get_host()+'/.*',refer)
        except KeyError, e:
            return HttpResponseRedirect('/')
            # pass
        except Exception:
            raise

        if a:
            book_title = request.GET['title']
            try:

                b = Book.objects.get(title=book_title)
                res = Recherche.objects(book=b)[0]

                if datetime.datetime.now().date() != res.day .date():
                    res = Recherche(book=b, nb_searches=1)
                else:
                    res.nb_searches += 1
                # import pdb;pdb.set_trace()
                res.save()
                return HttpResponseRedirect('../details/'+book_title[:32])
            except Book.DoesNotExist, e:
                return render_to_response('doesnotexist.html',RequestContext(request,{'title': book_title}))
            except Exception:
                raise
        else:
            return HttpResponseRedirect('/')

    elif request.method == 'POST':
        if request.user.is_authenticated() and request.GET:
            book_title = request.GET['title']
            # computeEmail(request.user.username,book_title)
            try:
                b = Book.objects.get(title=book_title)
            except Book.DoesNotExist, e:
                if not create_book(book_title):
                    b = Book.objects.get(title=book_title)
            except Exception:
                raise
            return HttpResponseRedirect('../details/'+book_title[:32])
            
@login_required
def book_detail(request, book_title):
    b = Book.objects.get(small_title=book_title)
    res = Recherche.objects(book=b)[0]
    if not b:
        return HttpResponseRedirect('/')        
    u_b = UniqueBook.objects(book=b)[0]
    # import pdb;pdb.set_trace()
    return render_to_response('book_details.html',RequestContext(request,{'title': b.title, 'img_url': u_b.image, 
        'nb_searches': res.nb_searches}))

def check_exist(request, book_title):
    for b in Book.objects:
        pass

def check_ask(request):
    if request.method == 'POST':
        return HttpResponseRedirect('/')