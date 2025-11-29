from django.urls import path
from .views import PostView, PostUpdateDeleteView, AllPostView, PostLikeView, CommentView , EmployeePostsByIdView

urlpatterns = [
    path('posts/', PostView.as_view(), name='employee-posts'),
    path('posts/<int:pk>/', PostUpdateDeleteView.as_view(), name='post-update-delete'),
    path('posts/employee/<int:employee_id>/', EmployeePostsByIdView.as_view(), name='specific-employee-all-posts'),
    path('all-posts/', AllPostView.as_view(), name='all-posts'),
    path('posts/<int:pk>/like/', PostLikeView.as_view(), name='post-like'),
    path('posts/liked/', PostLikeView.as_view(), name='all-liked-post'),
    path('posts/<int:pk>/comments/', CommentView.as_view(), name='post-comments'),
    path('comments/<int:pk>/', CommentView.as_view(), name='comment-update-delete'),
   
]
