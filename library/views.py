from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.utils.http import is_safe_url
from django.views import generic
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic.edit import UpdateView

from .models import *
from .forms import *

import math


def index(request, page=1):
    book_per_page = 15
    nb_books = Book.objects.count()
    first = (page - 1) * book_per_page
    last = min(first + book_per_page, nb_books)
    nb_pages = max(1, math.ceil(nb_books / book_per_page))
    min_next_page = max(1, page - 5)
    max_next_page = min(nb_pages, page + 5)
    if min_next_page == 1:
        max_next_page = min(nb_pages, 10)
    if max_next_page == nb_pages:
        min_next_page = max(1, nb_pages - 10)

    if page >= 1 and page <= nb_pages:
        latest_books_list = Book.objects.filter(status=1).order_by('-year_of_pub')[first:last]

        ratings = list()
        nb_ratings = list()
        for book in latest_books_list:
            rts = book.rating_set.all()
            if rts.count() == 0: avg_rating = 0
            else: avg_rating = sum([r.evaluation for r in rts]) / rts.count()
            ratings = ratings + [avg_rating]
            nb_ratings = nb_ratings + [rts.count()]

        context = {
            'nb_books': nb_books,
            'nb_books_displayed': last - first,
            'page': page,
            'nb_pages': nb_pages,
            'page_range': range(min_next_page, max_next_page + 1),
            'latest_books_list': zip(latest_books_list, ratings, nb_ratings),
            'prev_page': page - 1,
            'next_page': page + 1,
            'first_displayed': min(first + 1, last),
            'last_displayed': last,
        }
        return render(request, 'library/index.html', context)

    else:
        raise Http404

class SignUp(generic.CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('library:login')
    template_name = 'library/signup.html'

def profile(request, user):
    usr = get_object_or_404(CustomUser, username=user)
    own_profile = (user == request.user.username)
    if request.user.is_authenticated and not own_profile:
        friends1 = Friendship.objects.filter(sender=request.user).all()
        friends2 = Friendship.objects.filter(target=request.user).all()
        if len(friends1) > 0:
            if friends1[0].status == 1: friend_status = 1
            else: friend_status = 2
        elif len(friends2) > 0:
            if friends2[0].status == 1: friend_status = 1
            else: friend_status = 3
        else:
            friend_status = 4
    else:
        friend_status = 0

    if own_profile:
        requests = Friendship.objects.filter(target=request.user, status=0).all()
        nb_friend_requests = len(requests)
        recommendations = Recommendation.objects.filter(target=request.user).all()
        nb_recommendations = len(recommendations)
    else:
        nb_friend_requests = 0
        nb_recommendations = 0

    context = {
        'usr': usr,
        'own_profile': own_profile,
        'friend_status': friend_status,
        'nb_friend_requests': nb_friend_requests,
        'nb_recommendations': nb_recommendations,
        'nb_publication_req': Book.objects.filter(status=0).count(),
        'nb_publisher_req': CustomUser.objects.filter(authorization_level=2).count(),
        'nb_reports': Review.objects.filter(nb_reports__gte=5).count(),
    }
    return render(request, 'library/profile.html', context)

class CustomUserUpdate(UpdateView):
    model = CustomUser
    fields = ['address', 'email', 'privacy_level']
    template_name_suffix = '_update_form'

    def get_object(self):
        return get_object_or_404(CustomUser, username=self.request.user.username)

@login_required(redirect_field_name=None)
def modo_publisher_requests(request):
    if request.user.authorization_level == 4:
        context = {
            'requests': CustomUser.objects.filter(authorization_level=2).all(),
        }
        return render(request, 'library/modo_publisher_requests.html', context)
    else:
        return HttpResponseRedirect(
            reverse('library:profile', kwargs={'user':request.user.username})
        )

@login_required(redirect_field_name=None)
def modo_publication_requests(request):
    if request.user.authorization_level == 4:
        context = {
            'requests': Book.objects.filter(status=0).all(),
        }
        return render(request, 'library/modo_publication_requests.html', context)
    else:
        return HttpResponseRedirect(
            reverse('library:profile', kwargs={'user':request.user.username})
        )

@login_required(redirect_field_name=None)
def modo_review_reports(request):
    if request.user.authorization_level == 4:
        context = {
            'requests': Review.objects.filter(nb_reports__gte=5).all(),
        }
        return render(request, 'library/modo_review_reports.html', context)
    else:
        return HttpResponseRedirect(
            reverse('library:profile', kwargs={'user':request.user.username})
        )

@login_required(redirect_field_name=None)
def incr_balance(request, user):
    usr = request.user
    if usr.username == user:
        usr.balance += 100
        usr.save()
    return HttpResponseRedirect(
        reverse('library:profile', kwargs={'user':user})
    )

def bookdetails(request, bookid):
    book = get_object_or_404(Book, pk=bookid, status=1)
    owners = book.customuser_set.all()
    ratings = book.rating_set.all()
    nb_ratings = ratings.count()
    if nb_ratings == 0: avg_rating = 0
    else: avg_rating = sum([r.evaluation for r in ratings]) / nb_ratings
    try:
        reviews = Review.objects.filter(associated_rating__book__pk=bookid).order_by('date')
        nb_reviews = reviews.count()
    except ObjectDoesNotExist:
        nb_reviews = 0
    usr = request.user
    try:
        usr_rating = Rating.objects.get(user__username=usr.username,book__pk=bookid).evaluation
    except ObjectDoesNotExist:
        usr_rating = 0
    context = {
        'book': book,
        'nb_times_bought': owners.count(),
        'nb_ratings': nb_ratings,
        'avg_rating': avg_rating,
        'nb_reviews': nb_reviews,
        'usr_rating': usr_rating,
        'reviews': reviews,
        'owns_book': usr.is_authenticated and book in usr.books.all(),
    }
    return render(request, 'library/book.html', context)

@login_required(redirect_field_name=None)
def ratebook(request, bookid, rating):
    book = get_object_or_404(Book, pk=bookid, status=1)
    if rating >= 1 and rating <= 5:
        usr = request.user
        try:
            usr_rating = Rating.objects.get(user__username=usr.username,book__pk=bookid)
            usr_rating.evaluation = rating
            usr_rating.save()
        except ObjectDoesNotExist:
            new_rating = Rating(evaluation=rating, user=usr, book=book)
            new_rating.save()
    return HttpResponseRedirect(
        reverse('library:bookdetails', kwargs={'bookid':bookid})
    )

@login_required(redirect_field_name=None)
def buy_book(request, bookid):
    book = get_object_or_404(Book, pk=bookid, status=1)
    usr = request.user
    if request.method == 'POST':
        form = BuyBookForm(request.POST)
        if form.is_valid() and usr.balance >= book.price and book not in usr.books.all():
            usr.balance -= book.price
            usr.books.add(book)
            usr.save()
        return HttpResponseRedirect(reverse('library:bookdetails', kwargs={'bookid':bookid}))
    else:
        if usr.balance < book.price:
            status = 0
        elif book in usr.books.all():
            status = 1
        else:
            status = 2
        form = BuyBookForm()
    context = {
        'status': status,
        'book': book,
        'form': form,
    }
    return render(request, 'library/buy_book.html', context)

@login_required(redirect_field_name=None)
def recommend_book(request, bookid):
    book = get_object_or_404(Book, pk=bookid, status=1)
    usr = request.user
    status = 0

    friends1_q = Friendship.objects.filter(sender=usr, status=1)
    friends2_q = Friendship.objects.filter(target=usr, status=1)
    friends_choices = list()
    for friend in friends1_q | friends2_q:
        if friend.sender == usr: candidate = friend.target
        else: candidate = friend.sender
        if book not in candidate.books.all():
            if Recommendation.objects.filter(sender=usr, target=candidate, book=book).count() == 0:
                friends_choices += [(candidate.pk, candidate)]

    if request.method == 'POST':
        form = RecommendBookForm(request.POST, friends=friends_choices)
        if form.is_valid() and book in usr.books.all():
            status = 1
            target = get_object_or_404(CustomUser, pk=form.cleaned_data['friend'])
            recommendation = Recommendation(sender=usr, target=target, book=book)
            recommendation.save()
        else:
            status = 2
    else:
        form = RecommendBookForm(friends=friends_choices)
        if len(friends_choices) == 0:
            status = 3
    context = {
        'book': book,
        'form': form,
        'status': status,
    }
    return render(request, 'library/recommend_book.html', context)

def user_books(request, user):
    usr = get_object_or_404(CustomUser, username=user)
    if usr.privacy_level == 0 or (request.user.is_authenticated and usr.privacy_level == 1) or request.user.authorization_level == 4:
        books = usr.books.filter(status=1)

        ratings = list()
        nb_ratings = list()
        for book in books:
            rts = book.rating_set.all()
            if rts.count() == 0: avg_rating = 0
            else: avg_rating = sum([r.evaluation for r in rts]) / rts.count()
            ratings = ratings + [avg_rating]
            nb_ratings = nb_ratings + [rts.count()]

        context = {
            'usr': usr,
            'books': zip(books, ratings, nb_ratings),
        }
        return render(request, 'library/user_books.html', context)
    else:
        return HttpResponseRedirect(reverse('library:profile', kwargs={'user':user}))


@login_required(redirect_field_name=None)
def user_recommendations(request, user):
    usr = get_object_or_404(CustomUser, username=user)
    if user == usr.username:
        recommendations = Recommendation.objects.filter(target=usr).all()
        context = {
            'usr': usr,
            'recommendations': recommendations,
        }
        return render(request, 'library/user_recommendations.html', context)
    else:
        return HttpResponseRedirect(reverse('library:profile', kwargs={'user':user}))


def user_published_books(request, user):
    usr = get_object_or_404(CustomUser, username=user)
    if usr.privacy_level == 0 or (request.user.is_authenticated and usr.privacy_level == 1) or request.user.authorization_level == 4:
        books = Book.objects.filter(author=usr)

        ratings = list()
        nb_ratings = list()
        for book in books:
            rts = book.rating_set.all()
            if rts.count() == 0: avg_rating = 0
            else: avg_rating = sum([r.evaluation for r in rts]) / rts.count()
            ratings = ratings + [avg_rating]
            nb_ratings = nb_ratings + [rts.count()]

        context = {
            'usr': usr,
            'books': zip(books, ratings, nb_ratings),
            'own_profile': (usr == request.user),
        }
        return render(request, 'library/user_published_books.html', context)
    else:
        return HttpResponseRedirect(reverse('library:profile', kwargs={'user':user}))


@login_required(redirect_field_name=None)
def send_friend_request(request, user):
    usr = get_object_or_404(CustomUser, username=user)
    friends1 = Friendship.objects.filter(sender=usr, target=request.user)
    friends2 = Friendship.objects.filter(target=usr, sender=request.user)
    if usr != request.user and (friends1 | friends2).count() == 0:
        request = Friendship(sender=request.user, target=usr)
        request.save()
    return HttpResponseRedirect(reverse('library:profile', kwargs={'user':user}))

@login_required(redirect_field_name=None)
def delete_friend(request, user):
    usr = get_object_or_404(CustomUser, username=user)
    friends1 = Friendship.objects.filter(sender=usr, target=request.user, status=1)
    friends2 = Friendship.objects.filter(target=usr, sender=request.user, status=1)
    friends = friends1 | friends2
    if friends.count() > 0:
        friends[0].delete()
    return HttpResponseRedirect(reverse('library:profile', kwargs={'user':user}))

@login_required(redirect_field_name=None)
def accept_friend_request(request, user):
    usr = get_object_or_404(CustomUser, username=user)
    try:
        request = Friendship.objects.get(sender=usr, target=request.user, status=0)
        request.status = 1
        request.save()
    except ObjectDoesNotExist:
        pass
    return HttpResponseRedirect(reverse('library:profile', kwargs={'user':user}))

@login_required(redirect_field_name=None)
def reject_friend_request(request, user):
    usr = get_object_or_404(CustomUser, username=user)
    try:
        request = Friendship.objects.get(sender=usr, target=request.user, status=0)
        request.delete()
    except ObjectDoesNotExist:
        pass
    return HttpResponseRedirect(reverse('library:profile', kwargs={'user':user}))


@login_required(redirect_field_name=None)
def user_friends(request, user):
    if request.user.username == user:
        usr = get_object_or_404(CustomUser, username=user)
        friends1_q = Friendship.objects.filter(sender=usr, status=1)
        friends2_q = Friendship.objects.filter(target=usr, status=1)
        requests_q = Friendship.objects.filter(target=usr, status=0)

        friends = list()
        for friend in friends1_q | friends2_q:
            if friend.sender == usr: friends = friends + [friend.target]
            else: friends = friends + [friend.sender]
        requests = [u.sender for u in requests_q]

        context = {
            'requests': requests,
            'friends': friends,
            'nb_friends': len(friends),
        }
        return render(request, 'library/user_friends.html', context)
    else:
        return HttpResponseRedirect(reverse('library:profile', kwargs={'user':user}))

@login_required(redirect_field_name=None)
def publish_book(request, user):
    usr = request.user
    if user == usr.username and usr.authorization_level >= 3:
        if request.method == 'POST':
            form = CreateBookForm(request.POST)
            if form.is_valid():
                b = Book(
                    isbn = form.cleaned_data['isbn'],
                    title = form.cleaned_data['title'],
                    author = usr,
                    author_pseudonym = form.cleaned_data['author_pseudonym'],
                    price = form.cleaned_data['price'],
                    year_of_pub = form.cleaned_data['year_of_pub'],
                    image_url = form.cleaned_data['image_url'],
                    category = form.cleaned_data['category'],
                )
                b.save()
            return HttpResponseRedirect(reverse('library:user_published_books', kwargs={'user':user}))
        else:
            form = CreateBookForm()
        context = { 'form': form }
        return render(request, 'library/create_book.html', context)
    else:
        return HttpResponseRedirect(reverse('library:profile', kwargs={'user':user}))

@login_required(redirect_field_name=None)
def request_publisher(request, user):
    usr = request.user
    if user == usr.username and usr.authorization_level == 1:
        usr.authorization_level = 2
        usr.save()
    return HttpResponseRedirect(reverse('library:profile', kwargs={'user':user}))

@login_required(redirect_field_name=None)
def block_user(request, user):
    usr = get_object_or_404(CustomUser, username=user)
    if request.user.authorization_level == 4 and usr.authorization_level < 4:
        usr.authorization_level = 0
        usr.save()
    return HttpResponseRedirect(reverse('library:profile', kwargs={'user':user}))

@login_required(redirect_field_name=None)
def unblock_user(request, user):
    usr = get_object_or_404(CustomUser, username=user)
    if request.user.authorization_level == 4 and usr.authorization_level == 0:
        usr.authorization_level = 1
        usr.save()
    return HttpResponseRedirect(reverse('library:profile', kwargs={'user':user}))

@login_required(redirect_field_name=None)
def accept_publisher_request(request, user):
    usr = get_object_or_404(CustomUser, username=user)
    if request.user.authorization_level == 4 and usr.authorization_level == 2:
        usr.authorization_level = 3
        usr.save()
    return HttpResponseRedirect(reverse('library:profile', kwargs={'user':user}))

@login_required(redirect_field_name=None)
def reject_publisher_request(request, user):
    usr = get_object_or_404(CustomUser, username=user)
    if request.user.authorization_level == 4 and usr.authorization_level == 2:
        usr.authorization_level = 1
        usr.save()
    return HttpResponseRedirect(reverse('library:profile', kwargs={'user':user}))

@login_required(redirect_field_name=None)
def accept_publication(request, bookid):
    book = get_object_or_404(Book, pk=bookid)
    if request.user.authorization_level == 4 and book.status == 0:
        book.status = 1
        book.save()
    return HttpResponseRedirect(reverse('library:user_published_books', kwargs={'user':book.author.username}))

@login_required(redirect_field_name=None)
def reject_publication(request, bookid):
    book = get_object_or_404(Book, pk=bookid)
    if request.user.authorization_level == 4 and book.status == 0:
        book.status = 2
        book.save()
    return HttpResponseRedirect(reverse('library:user_published_books', kwargs={'user':book.author.username}))

@login_required(redirect_field_name=None)
def delete_book(request, bookid):
    book = get_object_or_404(Book, pk=bookid)
    if request.user.authorization_level == 4:
        book.status = 2
        book.save()
    return HttpResponseRedirect(reverse('library:index'))

@login_required(redirect_field_name=None)
def vote_review(request, reviewid, bookid, vote):
    rev = get_object_or_404(Review, pk=reviewid)
    if request.user.authorization_level >= 1 and not rev.voters.filter(username=request.user.username).exists():
        if vote == "up":
            rev.nb_likes += 1
        else:
            rev.nb_likes -= 1
        rev.voters.add(request.user)
        rev.save()
    return HttpResponseRedirect(reverse('library:review_details', kwargs={'reviewid':reviewid,'bookid':bookid}))

@login_required(redirect_field_name=None)
def comment_review(request, reviewid, bookid):
    rev = get_object_or_404(Review, pk=reviewid)
    if request.user.authorization_level >= 1:
        if request.method == 'POST':
            form = WriteCommentForm(request.POST)
            if form.is_valid():
                c = Comment(
                    content = form.cleaned_data['content'],
                    parent_review = rev,
                    user = request.user,
                )
                c.save()
        else:
            form = WriteCommentForm()
            context = { 'form': form }
            return render(request, 'library/write_comment.html', context)
    return HttpResponseRedirect(reverse('library:review_details', kwargs={'reviewid':reviewid,'bookid':bookid}))


@login_required(redirect_field_name=None)
def write_review(request, bookid):
    usr = request.user
    book = get_object_or_404(Book, pk=bookid)
    if usr.authorization_level >= 1 and Review.objects.filter(associated_rating__book=book, associated_rating__user=usr).count() == 0:
        if request.method == 'POST':
            form = WriteReviewForm(request.POST)
            if form.is_valid():
                try:
                    rating = Rating.objects.get(user=usr, book=book)
                    rating.evaluation = form.cleaned_data['evaluation']
                except ObjectDoesNotExist:
                    rating = Rating(
                        evaluation = form.cleaned_data['evaluation'],
                        user = usr,
                        book = book,
                    )
                rating.save()
                rev = Review(
                    content = form.cleaned_data['content'],
                    summary = form.cleaned_data['summary'],
                    associated_rating = rating,
                )
                rev.save()
            return HttpResponseRedirect(reverse('library:bookdetails', kwargs={'bookid':bookid}))
        else:
            try:
                rating = Rating.objects.get(user=usr, book=book)
                evalt = rating.evaluation
            except ObjectDoesNotExist:
                evalt = 3
            form = WriteReviewForm(default_eval=evalt)
        context = { 'form': form, 'book': book }
        return render(request, 'library/write_review.html', context)
    else:
        return HttpResponseRedirect(reverse('library:bookdetails', kwargs={'bookid':bookid}))

@login_required(redirect_field_name=None)
def delete_review(request, bookid, reviewid):
    usr = request.user
    rev = get_object_or_404(Review, pk=reviewid)
    author = rev.associated_rating.user
    if usr.authorization_level == 4 or usr == author:
        rev.delete()
    return HttpResponseRedirect(reverse('library:bookdetails', kwargs={'bookid':bookid}))

@login_required(redirect_field_name=None)
def report_review(request, bookid, reviewid):
    usr = request.user
    rev = get_object_or_404(Review, pk=reviewid)
    author = rev.associated_rating.user
    if usr.authorization_level < 4 and usr != author:
        rev.nb_reports += 1
        rev.save()
    return HttpResponseRedirect(reverse('library:bookdetails', kwargs={'bookid':bookid}))

def review_details(request, bookid, reviewid):
    rev = get_object_or_404(Review, pk=reviewid)
    context = { 'review': rev, 'bookid': bookid }
    return render(request, 'library/review_details.html', context)
