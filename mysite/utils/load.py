import json
import csv
from pathlib import Path
from collections import defaultdict
import numpy as np 

PARENT_DIR = Path(__file__).parent

REVIEWS_JSON = str(PARENT_DIR / 'rottenTomatoes/reviews.json')
REVIEWERS_CSV = str(PARENT_DIR / 'reviewers.csv')
MOVIES_CSV = str(PARENT_DIR / 'movies.csv')
RATINGS_CSV = str(PARENT_DIR / 'ratings.csv')

nREVIEWS_PER_REVIEWER_THRESHOLD = 50 # 60th percentile of 3221 reviewers scraped
nREVIEWS_PER_MOVIE_THRESHOLD = 2 # 40th percentile of 26126 movies scraped

def read_raw_json_input(file = REVIEWS_JSON):
    reviewers = defaultdict(list)
    movies = defaultdict(list)
    with open(file, 'r') as f:
        data = json.load(f)
        for d in data:
            #increment review count
            if (d['reviewer'], d['org']) not in reviewers:
                reviewers[(d['reviewer'], d['org'])] = [1,[]]
            else:
                reviewers[(d['reviewer'], d['org'])][0] += 1
            #append review
            reviewers[(d['reviewer'], d['org'])][1].append((d['title'], d['year'], d['rating']))
            #increment movie count
            if (d['title'], d['year']) not in movies:
                movies[(d['title'], d['year'])] = [1]
            else:
                movies[(d['title'], d['year'])][0] +=1

    n_reviewers = len(reviewers)
    n_movies = len(movies)
    reviewCounts = np.zeros(n_reviewers)
    for i, (key, value) in enumerate(reviewers.items()):
        reviewCounts[i] = value[0]

    print("{} reviewers".format(n_reviewers))
    print("{} movies".format(n_movies))

    f.close()
    return reviewers, reviewCounts, movies

# Gives int ids to reviewers, movies
# Doesn't give ids to reviewers, movies with review counts < threshold
def preprocess(reviewers, reviewCounts, movies):
    movies_ids = []
    reviewers_ids = []
    movies_set = set((str,str))
    for reviewer, li in reviewers.items():
        if li[0] < nREVIEWS_PER_REVIEWER_THRESHOLD:
            for review in li[1]:
                movies[tuple(review[:-1])][0] -= 1
        else:
            reviewers_ids.append(reviewer)
            li.insert(0, len(reviewers_ids) - 1)

    for movie in movies:
        if movies[movie][0] >= nREVIEWS_PER_MOVIE_THRESHOLD:
            movies_ids.append(movie)
            movies[movie].insert(0, len(movies_ids) - 1)
            movies_set.add(movie)

    return reviewers_ids, movies_ids, movies_set

def write_reviews_to_files(reviewers_ids, movies_ids, reviewers, movies, movies_set):
    with open(REVIEWERS_CSV, 'w', newline='') as reviewers_csv, \
        open(MOVIES_CSV, 'w', newline='') as movies_csv, \
        open(RATINGS_CSV, 'w', newline='') as ratings_csv:

        reviewers_writer = csv.writer(reviewers_csv)
        movies_writer = csv.writer(movies_csv)
        ratings_writer = csv.writer(ratings_csv)
        
        reviewers_header = ['id', 'name', 'org']
        reviewers_writer.writerow(reviewers_header)
        movies_header = ['id', 'title', 'year']
        movies_writer.writerow(movies_header)
        ratings_header = ['reviewer id', 'movie id', 'binarized rating']
        ratings_writer.writerow(ratings_header)
        
        for i, reviewer in enumerate(reviewers_ids):
            reviewers_row = list(reviewer)
            reviewers_row.insert(0, i)
            reviewers_writer.writerow(reviewers_row)
            for review in reviewers[reviewer][2]:
                if tuple(review[:-1]) in movies_set:
                    movie_id = movies[tuple(review[:-1])][0]
                    rating = review[-1]
                    num_rating = 1 #fresh
                    if rating == 'rotten':
                        num_rating = -1
                    ratings_writer.writerow([i, movie_id, num_rating])

        for i, movie in enumerate(movies_ids):
            movies_row = list(movie)
            movies_row.insert(0, i)
            movies_writer.writerow(movies_row)

    reviewers_csv.close()
    movies_csv.close()
    ratings_csv.close()

# Gets percentiles for nReviews per reviewer, movie to choose a threshold (no model, trial and error)
def percentiles(nparr_of_movies_or_reviewers):
    p_to_compute = [5, 10, 20, 30, 40, 50, 60, 70, 80, 85, 90, 95]
    print("Loading...")
    percentiles = np.percentile(nparr_of_movies_or_reviewers,  p_to_compute)
    print(percentiles)

# Reads in raw json review file, preprocesses reviews and writes cleaned data to csv files, loads csv files into 
# np ratings matrix
def load_ratings_matrix():
    reviewers, reviewCounts, movies = read_raw_json_input()
    reviewers_ids, movies_ids, movies_set = preprocess(reviewers, reviewCounts, movies)
    write_reviews_to_files(reviewers_ids, movies_ids, reviewers, movies, movies_set)

    n_reviewers = len(reviewers_ids)
    n_movies = len(movies_ids)
    ratings_mat = np.zeros((n_reviewers, n_movies))

    with open(RATINGS_CSV) as f:
        reader = csv.reader(f, ) 
        next(reader)
        for line in reader:
            ratings_mat[int(line[0])][int(line[1])] = int(line[2])
    f.close()
    return ratings_mat

def main():
    load_ratings_matrix()

if __name__ == "__main__":
    main()