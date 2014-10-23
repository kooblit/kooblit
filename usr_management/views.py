# -*- coding: utf-8 -*-
from random import randrange
import hashlib
import re

from django.shortcuts import render, render_to_response
from django.http import HttpResponseRedirect, HttpResponse, Http404

# from django.contrib.auth.forms import UserCreationForm
from .forms import UserCreationFormKooblit, ReinitialisationForm, DoReinitialisationForm
from django.contrib.auth.models import User
from .models import Verification, UserKooblit, Reinitialisation, Syntheses, Address
from manage_books_synth.models import Book
from django.contrib.auth import authenticate, login
from django.utils.datastructures import MultiValueDictKeyError
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

# Emails
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context

# Messages
from django.contrib import messages

# JSON
import json

from django.template import RequestContext

# Gestion du panier
from achat.utils import add_to_cart

email_adresse_regex = "[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
email_match = re.compile(email_adresse_regex)

def computeEmail(username, email, validation_id):
    htmly = get_template('email.html')
    d = Context({'username': username, 'validation_id': validation_id})
    subject, from_email, to = ('Welcome to Kooblit!!',
                               'no-reply@mail.kooblit.com', email)
    html_content = htmly.render(d)
    msg = EmailMultiAlternatives(subject, html_content, from_email, [to])
    msg.content_subtype = "html"
    msg.send()


def computeEmail_reinitialisation(username, email, validation_id):
    htmly = get_template('email_reinitialisation.html')
    d = Context({'username': username, 'validation_id': validation_id})
    subject, from_email, to = ('[Kooblit] Réinitialisation de mot de passe',
                               'noreply@kooblit.com', email)
    html_content = htmly.render(d)
    msg = EmailMultiAlternatives(subject, html_content, from_email, [to])
    msg.content_subtype = "html"
    msg.send()


def computeNewValidation(username):
    user = UserKooblit.objects.get(username__iexact=username)
    val = Verification(user=user, verification_id=hashlib.sha256(username).hexdigest())
    val.save()
    return val


def try_login(request, username, password, next_url, form):
    login_error = "Mauvais mot de passe ou identifiant"
    is_email = email_match.match(username) != None
    if is_email:
        try:
            user_kooblit = UserKooblit.objects.get(email=username)
        except UserKooblit.DoesNotExist:
            return render(request, 'inscription.html', {
                'form': form, 'next_url': next_url, 'login_error': login_error
                })
    else:
        username = username.lower()
        try:
            user_kooblit = UserKooblit.objects.get(username__iexact=username)
        except UserKooblit.DoesNotExist:
            return render(request, 'inscription.html', {
                'form': form, 'next_url': next_url, 'login_error': login_error
                })

    username = user_kooblit.username
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active and user_kooblit.is_confirmed:
            login(request, user)
            return HttpResponseRedirect(next_url)
        elif not user.is_active:
            messages.error(request, "Votre compte est désactivé.")
        else:
            messages.warning(request, "Vous devez activer votre compte. <a href='/accounts/renvoi'> Renvoi </a>")
        return HttpResponseRedirect('/', RequestContext(request))
    else:
        return render(request, 'inscription.html', {
            'form': form, 'next_url': next_url, 'login_error': login_error
            })

def contact(request):
    try:
        next_url = request.GET['next']
    except MultiValueDictKeyError:
        next_url = "/"

    if not request.user.is_authenticated():
        if request.method == 'POST':  # If the form has been submitted...
            form = UserCreationFormKooblit(request.POST)  # A form bound to the POST data

            # Check if it's a login
            try:
                username = request.POST['username_log']
                password = request.POST['password_log']
                return try_login(request, username, password, next_url, form)
            except MultiValueDictKeyError:
                pass

            # New user
            if form.is_valid():  # All validation rules pass
                username = form.cleaned_data.get("username")
                password = form.cleaned_data.get("password1")
                email = form.cleaned_data.get("email")
                form.save()
                val = computeNewValidation(username)
                computeEmail(username, email, val.verification_id)
                messages.success(request, "Félicitation. Un email de confirmation vous a été envoyé.\
                    Vous ne pourrez vous connecter qu'après y avoir jeté un coup d'oeil")
                return HttpResponseRedirect(next_url, RequestContext(request))

        else:
            form = UserCreationFormKooblit()  # An unbound form

        return render(request, 'inscription.html', {
            'form': form, 'next_url': next_url,
            })
    else:
        return HttpResponseRedirect(next_url)


# Lecture des syntheses
def can_read(id_synthese, username):
    synthese = Syntheses.objects.get(id=id_synthese)
    buyer = UserKooblit.objects.get(username=username)
    return synthese.user.username == username or synthese in buyer.syntheses.all()


@login_required
def lire_synthese(request, synthese_id):
    username = request.user.username
    if can_read(synthese_id, username):
        synt = Syntheses.objects.get(id=synthese_id)
        return render(request, 'lecture.html', RequestContext(request, {'synth': synt}))
    else:
        raise Http404()


# Use the login_required() decorator to ensure only those logged in can access the view.
@login_required
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)

    # Take the user back to the homepage.
    return HttpResponseRedirect('/')


def email_confirm(request, verification_id):
    try:
        val = Verification.objects.get(verification_id=verification_id)
        if val.user.is_active:
            val.user.is_confirmed = True
            val.user.save()
            # TODO: clean: unused password
            username = val.user.username
            password = val.user.password
            val.delete()

            user = User.objects.get(username__iexact=username)
            if user is not None:
                if user.is_active:
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(request, user)
                    messages.success(request, 'Votre compte Kooblit est activé!')
                    return HttpResponseRedirect('/', RequestContext(request))
            messages.error(request, "Votre compte kooblit est désactivé.")
            return HttpResponseRedirect('/', RequestContext(request))
        else:
            messages.error(request, "Votre compte kooblit est désactivé.")
            return HttpResponseRedirect('/', RequestContext(request))
    except Verification.DoesNotExist:
        raise Http404()


@login_required
def user_suppression(request):
    user = request.user
    user.delete()
    return HttpResponseRedirect('/')  # Redirect after POST


def get_syntheses_properties(syntheses):
    return [{
                "id": synth.id,
                "book_title": Book.objects.get(id=synth.livre_id).title,
                "author": synth.user.username,
                "prix": synth.prix,
                "nb_achat": synth.nb_achat,
                "note_moy": synth.note_moyenne,
                "gain": synth.nb_achat * synth.prix / 2,
            } for synth in syntheses]

@add_to_cart
def syntheses_from_user(request, username):
    try:
        user = UserKooblit.objects.get(username__iexact=username)
    except UserKooblit.DoesNotExist:
        raise Http404()
    syntheses = Syntheses.objects.filter(user=user)
    bought = []
    for synth in syntheses:
        bought.append(request.user.is_authenticated() and not synth.can_be_added_by(request.user.username))
    content = zip(syntheses, bought)
    return render_to_response(
        'synth_list_user.html',
        RequestContext(request, {'content': content}))

@login_required
def user_profil(request, username):
    user_kooblit = UserKooblit.objects.get(username__iexact=username)
    if user_kooblit.is_active and user_kooblit.is_confirmed:
        if request.user.username == username:
            if request.method == "POST":
                print request.POST
                return HttpResponse()
            else:
                syntheses_achetees = get_syntheses_properties(user_kooblit.syntheses.all())
                syntheses_ecrites = [
                            {
                                "id": synth.id,
                                "book_title": Book.objects.get(id=synth.livre_id).title,
                                "author": user_kooblit.username,
                                "prix": synth.prix,
                                "nb_achat": synth.nb_achat,
                                "note_moy": synth.note_moyenne,
                                "gain": synth.gain,
                            } for synth in Syntheses.objects.filter(user=user_kooblit, has_been_published=True)
                        ]
                syntheses_en_cours = [
                            {
                                "id": synth.id,
                                "book_title": Book.objects.get(id=synth.livre_id).title,
                                "author": user_kooblit.username,
                                "prix": synth.prix,
                                "nb_achat": synth.nb_achat,
                                "note_moy": synth.note_moyenne,
                                "gain": synth.gain,
                            } for synth in Syntheses.objects.filter(user=user_kooblit, has_been_published=False)
                        ]
                total = user_kooblit.cagnotte
                try:
                    adresse = Address.objects.get(user=user_kooblit)
                except Address.DoesNotExist:
                    adresse = ''
                return render(request, 'profil.html', RequestContext(request, {'user_kooblit': user_kooblit, 'adresse': adresse, 'syntheses_achetees': syntheses_achetees, 
                    'syntheses_ecrites': syntheses_ecrites, 'syntheses_en_cours': syntheses_en_cours, 'total': total}))
        else:
            return syntheses_from_user(request, username)
    else:
        raise Http404()


def check_exist(request):
    response_data = {}
    response_data['result'] = 'success'
    if request.method == 'GET':
        kwargs = {}
        username = request.GET.get('username', '')
        if not username:
            mail = request.GET.get('email', '')
            if not mail:
                return HttpResponse(json.dumps(response_data), content_type="application/json")
            kwargs['email'] = mail
        else:
            kwargs['username__iexact'] = username
        try:
            # TODO: clean: unused user_kooblit
            user_kooblit = UserKooblit.objects.get(**kwargs)
            response_data['result'] = 'failed'
            response_data['message'] = "L'utilisateur existe deja"
        except UserKooblit.DoesNotExist:
            pass
    return HttpResponse(json.dumps(response_data), content_type="application/json")

def resend_verification(request):
    if request.method == 'POST':
        form = ReinitialisationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            try:
                user = UserKooblit.objects.get(email=email)
            # TODO: Message d'erreur email does not exist
            except UserKooblit.DoesNotExist:
                return HttpResponseRedirect('/', RequestContext(request))
            # Recherche de la verification
            val = Verification.objects.get(user=user)
            username = user.username
            computeEmail(username, email, val.verification_id)
            messages.success(request, "Félicitation. Un email de confirmation vous a été envoyé.\
                    Vous ne pourrez vous connecter qu'après y avoir jeté un coup d'oeil")
            return HttpResponseRedirect('/', RequestContext(request))
        else:
            return render(request, 'ask_reinitialisation.html', RequestContext(request, {'form': form}))

    else:
        form = ReinitialisationForm()
        return render(request, 'ask_reinitialisation.html', RequestContext(request, {'form': form}))

def ask_reinitialisation(request):
    if request.method == 'POST':
        form = ReinitialisationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            user = UserKooblit.objects.get(email=email)
            # Suppression d'une demande si déjà existante
            reinits = Reinitialisation.objects.filter(user=user)
            for reinit in reinits:
                reinit.delete()
            try:
                while True:
                    x = randrange(2 ** 64)
                    rnd = hashlib.sha1(''.join((email, str(x)))).hexdigest()
                    Reinitialisation.objects.get(rnd=rnd)
            except Reinitialisation.DoesNotExist:
                pass
            user = UserKooblit.objects.get(email=email)
            r = Reinitialisation(user=user, rnd=rnd)
            r.save()
            computeEmail_reinitialisation(user.username, email, rnd)
            messages.success(request, "Un email vous a été renvoyé")
            return HttpResponseRedirect('/', RequestContext(request))
        else:
            return render(request, 'ask_reinitialisation.html', RequestContext(request, {'form': form}))

    else:
        form = ReinitialisationForm()
        return render(request, 'ask_reinitialisation.html', RequestContext(request, {'form': form}))


def do_reinitialisation(request, r_id):
    try:
        reinit = Reinitialisation.objects.get(rnd=r_id)
    except Reinitialisation.DoesNotExist:
        raise Http404()
    if request.method == 'GET':
        form = DoReinitialisationForm()
        return render(request, 'do_reinitialisation.html', RequestContext(request, {'form': form}))
    elif request.method == 'POST':
        form = DoReinitialisationForm(request.POST)
        if form.is_valid():
            user = reinit.user
            user.set_password(form.cleaned_data.get("mdp1"))
            user.save()
            reinit.delete()
            messages.success(request, 'Votre mot de passe a bien été changé')
            return HttpResponseRedirect('/', RequestContext(request))
        return render(request, 'do_reinitialisation.html', RequestContext(request, {'form': form}))

