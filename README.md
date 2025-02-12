# **Movie Recommender System Using Content Based Filtering**

**Access the website here:** https://free-movie-recommender.streamlit.app/

## **Definition of Recommender Systems**

Recommendation systems are a collection of algorithms used to recommend items to users based on information taken from the user. These systems have become ubiquitous, and can be commonly seen in online stores, movies databases and job finders. In this notebook, we will explore Content-based recommendation systems and implement a simple version of one using Python, Pandas library.

**Content Based Recommender Systems:** A Content-based recommender system tries to recommend items to users, based on their profile. The user's profile revolves around the user's preferences and tastes, or based on the user ratings.

## **Dependencies**

To follow along with this project, it's ideal to have the following library imported into a notebook in an IDE. We are using the Jupyter Notebook for this project, but any IDE would suffice. All we need is Pandas and a good knowledge of matrix-Algebra.

```import pandas as pd```


## **Project Structure**

### **Data Acquisition**
We shall use a public data set for movie ratings from [Kaggle.com](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata). The `tmdb_5000_credits.csv` and `tmdb_5000_movies.csv` data sets are available for your use in the root directory of this repo.

### **Data Cleaning and Pre-processing**
A summary of the tasks in this phase include:
- Fixing missing values
- Assigning proper headers
- Removing irrelevant features
- Applying descriptive Statistical moments
- One-Hot-Encoding categorical features and confirming proper data types

### **Content Based System**
Tasks here include:
- Creating User Profiles
- Extracting User's Preferences
- Learning the User Profile via Matrix-Algebra
- Building Recommendations
- Deploying the Recommender System

## **Summary**

### **Pros of Content-Based Recommender Systems**
- Learns user's preferences
- Highly personalized for the user

### **Cons of Content-Based Recommender Systems**
- Doesn't take into account what others think of the item, so low-quality item recommendations might happen
- Extracting data is not always intuitive
- Determining what characteristics of the item the user dislikes or likes is not always obvious
- No new genre of movies will ever get recommended to the user, except the user rates or indicates his/her preference for that genre

**A better solution is a Hybrid-Recommender-System that combines both Content-Based-Filtering and Collaborative-Filtering to proffer personalised as well as generally popular and preferred movies by Users who are similar to the User.**

## **License**

Items in this repo abide under the MIT License as seen in the root directory
