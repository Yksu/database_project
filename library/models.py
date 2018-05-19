import datetime

from django.db import models
from django.utils import timezone

from django.core.validators import RegexValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.urls import reverse, reverse_lazy



class CustomUser(AbstractUser):
    name_validator = RegexValidator(
        regex='^([a-zA-ZÀ-ÿ-.]|[a-zA-ZÀ-ÿ] [a-zA-ZÀ-ÿ])+$',
        message='This is not a valid name'
    )
    address_validator = RegexValidator(
        regex='^([a-zA-Z0-9À-ÿ -"\'.,;:&()])+$',
        message='This is not a valid address'
    )

    AUTHORIZATION_LEVEL_CHOICES = (
        (0, 'Blocked'),
        (1, 'Basic User'),
        (2, 'Publisher waiting for approval'),
        (3, 'Publisher'),
        (4, 'Moderator'),
    )
    PRIVACY_LEVEL_CHOICES = (
        (0, 'Profile open to anyone'),
        (1, 'Profile hidden to visitors'),
        (2, 'Profile hidden to everyone'),
    )

    first_name = models.CharField(blank=False, max_length=30, validators=[name_validator])
    last_name = models.CharField(blank=False, max_length=150, validators=[name_validator])
    address = models.CharField(blank=False, max_length=300, validators=[address_validator])
    email = models.CharField(blank=False, max_length=150)
    birthday = models.DateField()

    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    books = models.ManyToManyField('Book')
    friends = models.ManyToManyField('self', through='Friendship', related_name='friendship', symmetrical=False)
    book_recommendations = models.ManyToManyField('self', related_name='book_recommendation', through='Recommendation', symmetrical=False)

    authorization_level = models.IntegerField(choices=AUTHORIZATION_LEVEL_CHOICES, default=1)
    privacy_level = models.IntegerField(choices=PRIVACY_LEVEL_CHOICES, default=0)

    def __str__(self):
        return self.first_name + " " + self.last_name + " (" + self.username + ")"

    def get_absolute_url(self):
        return reverse('library:profile', kwargs={'user':self.username})


class Friendship(models.Model):
    def clean(self):
        super(Friendship, self).clean()
        if self.sender == self.target:
            raise ValidationError("A user cannot be friend with himself.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(Friendship, self).save(*args, **kwargs)

    FRIEND_STATUS_CHOICES = (
        (0, 'Waiting for approval'),
        (1, 'Accepted'),
    )

    sender = models.ForeignKey('CustomUser', related_name='sender', on_delete=models.CASCADE)
    target = models.ForeignKey('CustomUser', related_name='target', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(choices=FRIEND_STATUS_CHOICES, default=0)

    class Meta:
        unique_together = ('sender', 'target')

    def __str__(self):
        if self.status == 0:
            status_str = "Waiting for approval"
        else:
            status_str = "Accepted"
        return str(self.sender) + " -> " + str(self.target) + " | " + status_str


class Recommendation(models.Model):
    sender = models.ForeignKey('CustomUser', related_name='r_sender', on_delete=models.CASCADE)
    target = models.ForeignKey('CustomUser', related_name='r_target', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    book = models.ForeignKey('Book', on_delete=models.CASCADE)
    # TODO add a message with the recommendation

    def __str__(self):
        return str(self.sender) + " -> " + str(self.target) + " | " + str(self.book)



class Category(models.Model):
    """
    Category model
    """

    name = models.CharField(blank=False, max_length=20, unique=True)

    def __str__(self):
        return self.name



class Rating(models.Model):
    """
    Rating model
    """

    EVALUATION_CHOICES = [(i, i) for i in range(6)]

    date = models.DateTimeField(auto_now_add=True)
    evaluation = models.IntegerField(choices=EVALUATION_CHOICES)
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    book = models.ForeignKey('Book', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'book')

    def __str__(self):
        return str(self.user) + " | " + str(self.book) + " | " + str(self.evaluation) + "/5"




class Review(models.Model):
    """
    Review model
    """

    date = models.DateTimeField(auto_now_add=True)
    content = models.TextField('review', blank=False, max_length=5000)
    summary = models.CharField(blank=True, max_length=140)
    nb_likes = models.PositiveIntegerField('likes', default=0)
    nb_dislikes = models.PositiveIntegerField('dislikes', default=0)
    nb_reports = models.PositiveIntegerField('reports', default=0)
    voters = models.ManyToManyField('CustomUser')
    associated_rating = models.OneToOneField('Rating', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.associated_rating) + " | likes/dislikes: " + str(self.nb_likes) + "/" + str(self.nb_dislikes) + " | Review (" + str(len(self.content)) + " chars), summary: " + self.summary






class Comment(models.Model):
    """
    Comment model
    """

    date = models.DateTimeField(auto_now_add=True)
    content = models.TextField('comment', blank=False, max_length=1000)
    parent_review = models.ForeignKey('Review', on_delete=models.CASCADE)
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user) + " | likes/dislikes: " + str(self.nb_likes) + "/" + str(self.nb_dislikes) + " | " + self.content



class Book(models.Model):
    """
    Book model
    """

    BOOK_STATUS_CHOICES = (
        (0, 'Waiting for approval'),
        (1, 'Published'),
        (2, 'Removed'),
    )
    YEAR_CHOICES = []
    for y in range(datetime.datetime.now().year, 1900, -1):
        YEAR_CHOICES.append((y, y))

    ISBN_VALIDATOR = RegexValidator(
        '^([0-9]{3}-)?[0-9]-[0-9]{4}-[0-9]{4}-[0-9]$',
        'The ISBN has an invalid format'
    )
    IMAGE_URL_VALIDATOR = RegexValidator(
        '^(http(s)?:\/\/)?(www\.)?[a-zA-Z0-9\_\-\.]+([\-\.\/]{1}[a-zA-Z0-9\_\-\%\.]+)*\.(jpg|jpeg|png)$',
        'The image URL has an invalid format'
    )
    def AUTHOR_VALIDATOR(user):
        if not True:                                                                                    # TODO assert user is author
            raise ValidationError(
                _('User %(name)s is not an author and does not have permission to publish a book.'),
                params={'name': user.name}
            )

    isbn = models.CharField(
        'ISBN',
        primary_key=True,
        unique=True,
        help_text='ISBN format: either <em>X-XXXX-XXXX-X</em> or <em>XXX-X-XXXX-XXXX-X</em> where X is a digit',
        max_length=17,
        validators=[ISBN_VALIDATOR]
    )
    status = models.IntegerField(default=0, choices=BOOK_STATUS_CHOICES)
    title = models.CharField(blank=False, max_length=100)
    author = models.ForeignKey('CustomUser', on_delete=models.PROTECT, validators=[AUTHOR_VALIDATOR], blank=True, null=True)
    author_pseudonym = models.CharField(blank=False, max_length=50)
    price = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.0, 'The price must be positive.')])
    year_of_pub = models.IntegerField('year of publication', choices=YEAR_CHOICES)
    image_url = models.URLField(
        max_length=1000,
        help_text='Image format should be .jpg, .jpeg or .png',
        validators=[IMAGE_URL_VALIDATOR]
    )
    category = models.ForeignKey('Category', on_delete=models.PROTECT)

    def __str__(self):
        return self.title + " (" + self.category.name + ") by " + self.author_pseudonym + " (" + str(self.year_of_pub) + ") - $" + str(self.price)
