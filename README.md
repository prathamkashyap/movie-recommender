<!DOCTYPE html>
<html>
<head>
    <title>Movie Recommender System</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
        }
        h1 {
            font-size: 28px;
            font-weight: bold;
        }
        h2 {
            font-size: 22px;
            font-weight: bold;
            margin-left: 20px;
        }
        p, li {
            font-size: 16px;
            margin-left: 40px;
        }
    </style>
</head>
<body>
    <h1>Movie Recommender System Using Content-Based Filtering</h1>
    
    <p><strong>Access the website here:</strong> <a href="https://mmovierecommendersystem.herokuapp.com/">Movie Recommender</a></p>
    
    <h2>Definition of Recommender Systems:</h2>
    <p>Recommendation systems are a collection of algorithms used to recommend items to users based on information taken from the user. These systems have become ubiquitous, commonly seen in online stores, movie databases, and job finders. In this notebook, we will explore Content-based recommendation systems and implement a simple version using Python and Pandas.</p>
    
    <h2>Content-Based Recommender Systems:</h2>
    <p>A Content-based recommender system tries to recommend items to users based on their profile. The user’s profile revolves around the user’s preferences and tastes or based on the user ratings.</p>
    
    <h2>Dependencies:</h2>
    <p>To follow along with this project, it's ideal to have the following library imported into a notebook in an IDE.</p>
    <p><strong>Python Code:</strong></p>
    <pre><code>import pandas as pd</code></pre>
    
    <h2>Project Structure:</h2>
    <h2>1. Data Acquisition:</h2>
    <p>We shall use a public dataset for movie ratings from Kaggle.com. The <strong>tmdb_5000_credits.csv</strong> and <strong>tmdb_5000_movies.csv</strong> datasets are available in the root directory of this repo.</p>
    
    <h2>2. Data Cleaning and Pre-processing:</h2>
    <ul>
        <li>Fixing missing values.</li>
        <li>Assigning proper headers.</li>
        <li>Removing irrelevant features.</li>
        <li>Applying descriptive Statistical moments.</li>
        <li>One-Hot-Encoding categorical features and confirming proper data types.</li>
    </ul>
    
    <h2>3. Content-Based System:</h2>
    <ul>
        <li>Creating User Profiles.</li>
        <li>Extracting User's Preferences.</li>
        <li>Learning the User Profile via Matrix-Algebra.</li>
        <li>Building Recommendations.</li>
        <li>Deploying the Recommender System.</li>
    </ul>
    
    <h2>Summary:</h2>
    <h2>Pros and Cons of Content-Based Recommender Systems</h2>
    <h2>Pros:</h2>
    <ul>
        <li>Learns user’s preferences.</li>
        <li>Highly personalized for the user.</li>
    </ul>
    
    <h2>Cons:</h2>
    <ul>
        <li>Doesn’t take into account what others think of the item, so low-quality recommendations might happen.</li>
        <li>Extracting data is not always intuitive.</li>
        <li>Determining what characteristics of the item the user dislikes or likes is not always obvious.</li>
        <li>No new genre of movies will ever get recommended to the user unless the user rates or indicates preference for that genre.</li>
    </ul>
    
    <p>A better solution is a <strong>Hybrid-Recommender-System</strong> that combines both Content-Based-Filtering and Collaborative-Filtering to provide personalized as well as generally popular recommendations.</p>
    
    <h2>License:</h2>
    <p>Items in this repo abide under the MIT License as seen in the root directory.</p>
</body>
</html>
