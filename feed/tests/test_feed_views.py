import pytest
from feed.models import Post
from django.contrib.auth import authenticate
from django.contrib.auth.models import User


USERNAME1 = 'username1'
USERNAME2 = 'username2'
USER_PASS = 'secret_pass'
POST_TITLE = 'post title'
POST_CONTENT = 'some post content'
LOGIN_URL = '/login/'
POST_DETAIL_URL = '/post/'
FEED_URL = '/'
NEW_POST_URL = '/post/new/'
REDIRECT_URL_STATUS = 302
PAGE_NOT_FOUND = 404


def post_delete_url(post_id):
    return f"/post/{post_id}/delete/"


@pytest.fixture
def users(db):
    user1 = User.objects.create_user(USERNAME1, password=USER_PASS)
    user2 = User.objects.create_user(USERNAME2, password=USER_PASS)
    return [user1, user2]


@pytest.fixture
def post(db, users):
    post = Post.posts.create(title=POST_TITLE, content=POST_CONTENT, author=users[0])
    post.save()
    return post


@pytest.mark.django_db
class TestPostDetailView:
    def test_detail_view_page_entrypoint(self, post, client):
        # Testing to see if a valid post id gets a valid detail view page
        response = client.get(POST_DETAIL_URL + str(post.id) + '/')
        assert response.status_code == 200

    def test_detail_view_returned_data(self, post, client):
        # Testing that the returned post really is the one
        # that it ID has passed through the URL
        response = client.get(POST_DETAIL_URL + str(post.id) + '/')
        assert response.context['post'].id == post.id

    def test_detail_view_page_for_invalid_post_id(self, client):
        # Testing to see if for an invalid post id, the response will be 404
        # The id's start from 1 and increases by 1 for each post, so the last post will
        # get the id of the number of posts, so by adding 1 we promise that it will be
        # an invalid ID
        max_post_id = Post.posts.all().count()
        response = client.get(POST_DETAIL_URL + str(max_post_id + 1) + '/')
        assert response.status_code == PAGE_NOT_FOUND


class TestPostDeleteView:
    def test_delete_url_for_logged_out_user(self, post, client):
        # Testing to verify that when logged out user tryies to delete a post
        # the user gets a 302 response code and that the post remains
        post_to_delete = Post.posts.filter(title=post.title, content=post.content, author=post.author).first()
        response = client.get(post_delete_url(post_to_delete.id))
        assert response.status_code == 302
        assert post_to_delete in Post.posts.all()

    def test_delete_url_for_non_author_user(self, request, client, post):
        # Testing that if a logged in, non author, user tries to delete
        # a post, a 403 response will return
        post_to_delete = Post.posts.filter(title=post.title, content=post.content, author=post.author).first()
        non_author_user = authenticate(request, username=USERNAME2, password=USER_PASS)

        if non_author_user is not None:
            client.login(username=USERNAME2, password=USER_PASS)
            response = client.get(post_delete_url(post_to_delete.id))
            assert response.status_code == 403
        else:
            # The user login detail are wrong
            assert False

    def test_success_delete_using_delete_view(self, request, client, post):
        # Testing successfully deleting a post using the delete view via the delete post URL
        # Making sure the author of the post is logged in
        post_to_delete = Post.posts.filter(title=post.title, content=post.content, author=post.author).first()
        author = authenticate(request, username=USERNAME1, password=USER_PASS)
        assert post_to_delete in Post.posts.all()

        if author is not None:
            client.login(username=USERNAME1, password=USER_PASS)
            client.post(post_delete_url(post_to_delete.id))
            assert post_to_delete not in Post.posts.all()
        else:
            # The user login detail are wrong
            assert False


@pytest.mark.django_db
class TestPostCreateView:
    def test_create_new_post_view_entrypoin_auth(self, client, users):
        # Testing that for a logged in user, the new post url gets a valid response
        client.force_login(users[0])
        response = client.get(NEW_POST_URL)
        assert response.status_code == 200

    def test_create_new_post_view_entrypoint_unauth(self, client):
        # Testing that for logged out users, the create new post url
        # redirects to the login page
        response = client.get(NEW_POST_URL)
        assert response.status_code == REDIRECT_URL_STATUS
        assert response.url == LOGIN_URL + '?next=' + NEW_POST_URL

    def test_post_creation_using_form(self, users, client):
        # Testing that a post creates successfully using the create new
        # post form
        form_data = {'title': 'some title', 'content': 'some content...', }
        assert not Post.posts.filter(title=form_data['title'], content=form_data['content']).exists()
        client.force_login(users[0])
        client.post(NEW_POST_URL, form_data)
        assert Post.posts.filter(title=form_data['title'], content=form_data['content']).exists()

    def test_redirect_after_successful_post_creation(self, users, client):
        # Testing that after a successful post creation, the user gets
        # redirectd to the new post detail view page
        form_data = {'title': 'some title', 'content': 'some content...', }
        client.force_login(users[0])
        response = client.post(NEW_POST_URL, form_data)
        assert response.status_code == REDIRECT_URL_STATUS
        # The new post ID should be as the amount of posts exists
        new_post_id = Post.posts.count()
        assert response.url == POST_DETAIL_URL + str(new_post_id) + '/'
