from django.db import models

class User(models.Model):
    name = models.CharField(max_length = 30)

class Movie(models.Model):
    title = models.CharField(max_length = 30) 

#permits binary like/not like and five star
class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    
    STARS = [
        (5, '5'),
        (4, '4'),
        (3, '3'),
        (2, '2'),
        (1, '1'),
    ]

    BINARY = [
        (0, 'Dislike'),
        (1, 'Like'),
    ]

    starRating =  models.PositiveSmallIntegerField(max_length = 2, choices = STARS)
    binaryRatings = models.PositiveSmallIntegerField(max_length = 2, choices = BINARY)


