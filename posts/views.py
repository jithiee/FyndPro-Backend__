from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated , AllowAny
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Post, Like, Comment
from .serializers import PostSerializer, CommentSerializer


# ------------------ Employee Post APIs ------------------
class PostView(APIView):
    """
    Create and list posts for authenticated employee.
    Only users with role 'employee' can create posts.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]  # Content-Type: multipart/form-data upload files (like images, PDFs, videos) using a POST request, the request content type

    @swagger_auto_schema(
        tags=["Posts"],
        operation_summary="Get Employee's Posts",
        operation_description="Retrieve all posts created by the authenticated employee.",
        responses={200: PostSerializer(many=True)}
    )
    def get(self, request):
        posts = Post.objects.filter(user=request.user).select_related('user').prefetch_related('likes', 'comments')
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["Posts"],
        operation_summary="Create Post",
        operation_description="Create a new post. Only employees are allowed to create posts. "
                              "Upload files in 'post' field and add optional title & description.",
        request_body=PostSerializer,
        responses={
            201: PostSerializer,
            400: "Invalid data",
            403: "Only employees can create posts"
        }
    )
    def post(self, request):
        if request.user.role != 'employee':
            return Response({"error": "Only employees can create posts"}, status=status.HTTP_403_FORBIDDEN)
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ------------------ Update / Delete Post ------------------
class PostUpdateDeleteView(APIView):
    """
    Update or delete a post by the owner employee.
    """
    permission_classes = [IsAuthenticated]

    def get_post(self, pk):
        try:
            return Post.objects.get(pk=pk, user=self.request.user)
        except Post.DoesNotExist:
            return None

    @swagger_auto_schema(
        tags=["Posts"],
        operation_summary="Retrieve Single Post",
        operation_description="Retrieve a single post by its ID for the authenticated employee.",
        responses={200: PostSerializer, 404: "Post not found"}
    )
    def get(self, request, pk):
        post = self.get_post(pk)
        if not post:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = PostSerializer(post)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["Posts"],
        operation_summary="Update Post",
        operation_description="Update an existing post. Only the owner employee can update their post.",
        request_body=PostSerializer,
        responses={200: PostSerializer, 400: "Invalid data", 404: "Post not found"}
    )
    def put(self, request, pk):
        post = self.get_post(pk)
        if not post:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = PostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=["Posts"],
        operation_summary="Delete Post",
        operation_description="Delete a post. Only the owner employee can delete their post.",
        responses={204: "Post deleted successfully", 404: "Post not found"}
    )
    def delete(self, request, pk):
        post = self.get_post(pk)
        if not post:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)
        post.delete()
        return Response({"message": "Post deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    
    

# ------------------ Get All Posts by Specific Employee ------------------
class EmployeePostsByIdView(APIView):
    """
    Retrieve all posts created by a specific employee (using their user ID).
    """
    # permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=["Posts"],
        operation_summary="Get All Posts by Specific Employee",
        operation_description="Retrieve all posts created by a specific employee using their employee ID.",
        manual_parameters=[
            openapi.Parameter('employee_id', openapi.IN_PATH, description="Employee ID", type=openapi.TYPE_INTEGER)
        ],
        responses={200: PostSerializer(many=True), 404: "Employee not found or has no posts"}
    )
    def get(self, request, employee_id):
        posts = Post.objects.filter(user_id=employee_id).select_related('user').prefetch_related('likes', 'comments')
        if not posts.exists():
            return Response({"error": "No posts found for this employee"}, status=status.HTTP_404_NOT_FOUND)
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ------------------ All Posts View (Paginated) ------------------
class AllPostView(APIView):
    """
    Retrieve all posts from other employees, paginated.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Posts"],
        operation_summary="Get All Employee Posts (Paginated)",
        operation_description="Retrieve all posts from other employees, excluding authenticated user's posts. "
                              "Results are paginated with 5 posts per page.",
        responses={200: PostSerializer(many=True)}
    )
    def get(self, request):
        paginator = PageNumberPagination()
        paginator.page_size = 5
        posts = Post.objects.exclude(user=request.user).select_related('user').prefetch_related('likes', 'comments')
        result_page = paginator.paginate_queryset(posts, request)
        serializer = PostSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


# ------------------ Post Like / Unlike ------------------
class PostLikeView(APIView):
    """
    Like or unlike a post. Users cannot like their own posts.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Likes"],
        operation_summary="Like / Unlike Post",
        operation_description="Like a post if not already liked. Unlike if already liked. "
                              "Users cannot like their own posts.",
        responses={200: "Post liked/unliked", 403: "Cannot like own post", 404: "Post not found"}
    )
    def post(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        # if post.user == request.user:
        #     return Response({"error": "Cannot like your own post"}, status=status.HTTP_403_FORBIDDEN)

        like = Like.objects.filter(user=request.user, post=post).first()
        if like:
            like.delete()
            return Response({"msg": "Post unliked"})
        Like.objects.create(user=request.user, post=post)
        return Response({"msg": "Post liked"})
    
    @swagger_auto_schema(
        tags=["Likes"],
        operation_summary="Get All Liked Posts by User",
        operation_description="Retrieve all posts that the authenticated user has liked.",
        responses={200: PostSerializer(many=True)}
    )
    def get(self, request):
        liked_posts = Post.objects.filter(likes__user=request.user).select_related('user').prefetch_related('likes', 'comments')
        serializer = PostSerializer(liked_posts, many=True)
        return Response(serializer.data)
    
    

# ------------------ Comment APIs a post  Retrieve all comment, Update & Delete Single Comment ------------------
class CommentView(APIView):
    """
    List, create, update and delete comments for a specific post.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Comments"],
        operation_summary="Get Comments",
        operation_description="Retrieve all comments for a specific post, ordered by newest first.",
        responses={200: CommentSerializer(many=True)}
    )
    def get(self, request, pk):
        comments = Comment.objects.filter(post__pk=pk).select_related('user').order_by("-created_at")
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["Comments"],
        operation_summary="Add Comment",
        operation_description="Add a comment to a post. Users cannot comment on their own posts.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'text': openapi.Schema(type=openapi.TYPE_STRING, description="Comment text")
            },
            required=['text']
        ),
        responses={201: CommentSerializer, 400: "Invalid data", 403: "Cannot comment on own post", 404: "Post not found"}
    )
    def post(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        # if post.user == request.user:
        #     return Response({"error": "Cannot comment on your own post"}, status=status.HTTP_403_FORBIDDEN)

        serializer = CommentSerializer(data={'post': post.id, 'text': request.data.get('text')})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    @swagger_auto_schema(
        tags=["Comments"],
        operation_summary="Update Comment",
        operation_description="Update a comment. Only the comment owner can update it.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'text': openapi.Schema(type=openapi.TYPE_STRING, description="Updated comment text")
            },
            required=['text']
        ),
        responses={200: CommentSerializer, 403: "Permission denied", 404: "Comment not found"}
    )
    def put(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)

        if comment.user != request.user:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = CommentSerializer(comment, data={'text': request.data.get('text')}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=["Comments"],
        operation_summary="Delete Comment",
        operation_description="Delete a comment. Only the comment owner can delete it.",
        responses={204: "Comment deleted", 403: "Permission denied", 404: "Comment not found"}
    )
    def delete(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)
        if comment.user != request.user:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        comment.delete()
        return Response({"message": "Comment deleted"}, status=status.HTTP_204_NO_CONTENT)
























