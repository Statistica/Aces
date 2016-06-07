# Written by Jonathan Saewitz, released June 7th, 2016
# Released under the MIT License (https://opensource.org/licenses/MIT)

import requests, matplotlib.pyplot as plt, numpy, time, plotly.plotly as plotly, plotly.graph_objs as go
from datetime import datetime
from collections import Counter
from time import mktime
from wordcloud import WordCloud, STOPWORDS
from scipy.misc import imread
from collections import Counter

def get_ids(access_token):
	response=requests.get('https://graph.facebook.com/v2.6/%s/feed?access_token=%s' % ('893372457376394', access_token)).json()

	post_ids=[]

	for post in response['data']: #loop through the posts
		post_ids.append(post['id'])

	while 'paging' in response and 'next' in response['paging']:
		next_url=response['paging']['next'] #get the next paging url
		response=requests.get(next_url).json()
		posts=response['data']
		for post in posts: #loop through the posts
			post_ids.append(post['id'])
	return post_ids

def get_posts(access_token, post_ids):
	posts=[]
	for post_id in post_ids: #get post and likes for each post
		post=requests.get('https://graph.facebook.com/v2.6/%s?access_token=%s' % (post_id, access_token)).json()
		likes=requests.get('https://graph.facebook.com/v2.6/%s/likes?summary=true&access_token=%s' % (post_id, access_token)).json()['summary']['total_count']
		time_created=post['created_time'][:-5] #remove last 5 characters (usually "+0000")
		time_created=datetime.fromtimestamp(mktime(time.strptime(time_created, '%Y-%m-%dT%H:%M:%S')))
		try:
			posts.append({'id': post_id, 'message': post['message'], 'time': time_created, 'likes': likes})
		except Exception as e:
			print post_id + " is not a message post (e.g. event created or group settings changed)"
	return posts

def create_wordcloud(posts):
	wordcloud_str=' '.join(post['message'] for post in posts) #join all posts together
	aces_mask=imread("aces.png") #add aces mask
	wc=WordCloud(background_color="BLACK", mask=aces_mask, stopwords=STOPWORDS.add("will")) #don't include the word "will" in the wordcloud
																							#(not an interesting word and took up a large chunk of the wordcloud)
	wc.generate(wordcloud_str)
	plt.axis("off")
	plt.imshow(wc)
	plt.show()
	wc.to_file("aces_wordcloud.png")

def average_likes(posts):
	posts=sorted(posts, key=lambda f: f['likes']) #sort by number of likes
	print "Most liked post: " + posts[-1]['id'] + " (" + str(posts[-1]['likes']) + ")"

	median=numpy.median([post['likes'] for post in posts]) #get the median number of likes
	print "Median number of post likes: " + str(median)
	total_likes=0
	for post in posts: #loop through all of the posts,
		total_likes+=post['likes'] #adding up the total number of likes
		if post['likes']==median: #find the median number of likes post
			print "Median number of likes post: " + post['id']
	print "Number of posts: " + str(len(posts))
	print "Total number of likes: " + str(total_likes)
	print "Average number of likes (mean): " + str(float(total_likes)/len(posts))

def create_hour_like_heatmap(posts):
	times=[]
	for i in range(24): #add 24 hours to the times list
		times.append({"hour": + i, "likes": 0, "posts": 0})
	for post in posts: #loop through the posts
		for time in times: #loop through the times
			if post['time'].hour==time['hour']: #if the times are equal for the current post's time and the current loop's time:
				time['likes']+=post['likes']
				time['posts']+=1
				break #if we've found a match, break, since we already found the hour in times and we don't need to keep searching for it

	for time in times: #get the average number of likes
		if not time['posts']==0:
			time['avg_likes']=float(time['likes'])/time['posts']
		else: #to prevent division by 0
			time['avg_likes']=0

	data=[
		go.Heatmap(
			x=[time['hour'] for time in times],
			y=["Likes"]*24,
			z=[time['avg_likes'] for time in times]
		)
	]

	layout=go.Layout(
		title="Aces Nation Average Likes By Hour",
		xaxis=dict(
			title="Hour",
		)
	)

	fig=dict(data=data, layout=layout)
	plotly.plot(fig)

def create_day_like_heatmap(posts):
	times=[]
	for i in range(7):
		times.append({"day": + i, "likes": 0, "posts": 0})
		#0=Monday
		#...
		#6=Sunday

	for post in posts:
		for time in times:
			if post['time'].weekday()==time['day']:
				time['likes']+=post['likes']
				time['posts']+=1
				break #if we've found a match, break, since we already found the day in times and we don't need to keep searching for it

	for time in times: #get the average number of likes
		if not time['posts']==0:
			time['avg_likes']=float(time['likes'])/time['posts']
		else: #to prevent division by 0
			time['avg_likes']=0

	data=[
		go.Heatmap(
			x=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
			y=["Likes"]*7,
			z=[time['avg_likes'] for time in times] #add the average likes to the heatmap
		)
	]

	layout=go.Layout(
		title="Aces Nation Average Likes By Day Of Week",
		xaxis=dict(
			title="Hour",
		),
		yaxis=dict(
			title="Day of Week",
			autorange="reversed"
		)
	)

	fig=dict(data=data, layout=layout)
	plotly.plot(fig)

def create_day_and_hour_like_heatmap(posts):
	times=[]
	for i in range(7):
		for j in range(24):
			times.append({"day": + i, "hour": + j, "likes": 0, "posts": 0})
			#i=0=Monday
			#...
			#i=6=Sunday

	for post in posts:
		for time in times:
			if post['time'].weekday()==time['day'] and post['time'].hour==time['hour']: #if the time and hour of the looped post are equal
																						#to the time and hour of the looped time:
				time['likes']+=post['likes']
				time['posts']+=1
				break #if we've found a match, break, since we already found the day and hour in times and we don't need to keep searching for it

	times_list=[[], [], [], [], [], [], []] #create 7 empty list of times (one per day of week)

	for time in times:
		if not time['posts']==0:
			time['avg_likes']=float(time['likes'])/time['posts']
		else: #to prevent division by 0
			time['avg_likes']=0

		day=time['day'] #day=current looped time's day
		likes=time['avg_likes'] #likes=current looped time's average number of likes
		times_list[day].append(likes) #append the currently looped number of likes to the currently looped day

	data=[
		go.Heatmap(
			x=[i for i in range(24)], #add 24 numbers (0->23) to the x for hours
			y=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
			z=times_list
		)
	]

	layout=go.Layout(
		title="Aces Nation Average Likes By Day Of Week And Hour By Post",
		xaxis=dict(
			title="Hour",
		),
		yaxis=dict(
			title="Day of Week",
			autorange="reversed"
		)
	)

	fig=dict(data=data, layout=layout)
	plotly.plot(fig)

def get_comments(post_ids, access_token):
	comment_ids=[]

	for post_id in post_ids: #loop through the post ids
		response=requests.get('https://graph.facebook.com/v2.6/%s/comments?access_token=%s' % (post_id, access_token)).json() #get the comments for the current post id

		for comment in response['data']: #loop through the comments
			comment_ids.append(comment['id']) #add the comment ids

		while 'paging' in response and 'next' in response['paging']: #get more comments from the paging url (if necessary)
			next_url=response['paging']['next'] #get the next paging url
			response=requests.get(next_url).json()
			comments=response['data']
			for comment in comments: #loop through the comments
				comment_ids.append(comment['id'])

	return comment_ids

def average_comments(comment_ids, posts, access_token):
	comments=[]
	for comment_id in comment_ids: #loop through the comment ids
		#get the number of likes on the current comment id:
		likes=requests.get('https://graph.facebook.com/v2.6/%s/likes?summary=true&access_token=%s' % (comment_id, access_token)).json()['summary']['total_count']
		comments.append({'id': comment_id, 'likes': likes}) #append the number of likes to the comments list

	comments=sorted(comments, key=lambda f: f['likes']) #sort the comments by number of likes
	print "Most liked comment: " + comments[-1]['id'] + " (" + str(comments[-1]['likes']) + ")"

	median=numpy.median([comment['likes'] for comment in comments]) #get the median number of likes
	print "Median number of comment likes: " + str(median)
	total_likes=0
	for comment in comments: #loop through the comments,
		total_likes+=comment['likes'] #adding up the total number of likes
		if comment['likes']==median: #find the median number of comments post
			print "Median number of likes comment: " + comment['id']
	print "Number of comments: " + str(len(comments))
	print "Total number of likes: " + str(total_likes)
	print "Average number of likes (mean): " + str(float(total_likes)/len(comments))

	print "There are on average %s comments per post" % (float(len(comments))/len(posts))

access_token="" #obtain from https://developers.facebook.com/tools/explorer/
post_ids=get_ids(access_token)
posts=get_posts(access_token, post_ids)
create_wordcloud(posts)
average_likes(posts)
create_hour_like_heatmap(posts)
create_day_like_heatmap(posts)
create_day_and_hour_like_heatmap(posts)
comment_ids=get_comments(post_ids, access_token)
average_comments(comment_ids, posts, access_token)