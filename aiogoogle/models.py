from urllib.parse import urlparse, urlunparse, urlencode, parse_qs
import pprint

from .excs import HTTPError, AuthError


DEFAULT_DOWNLOAD_CHUNK_SIZE = 1024 * 1024
DEFAULT_UPLOAD_CHUNK_SIZE = 1024 * 1024


class ResumableUpload:
    """
    Resumable Upload Object. Works in conjuction with media upload 
    
    Arguments:

        file_path (str): Full path of the file to be uploaded
        
        upload_path (str): The URI path to be used for upload. Should be used in conjunction with the rootURL property at the API-level.
        
        multipart (bool): True if this endpoint supports upload multipart media.

        chunksize (int): Size of a chunk of bytes that a session should read at a time when uploading in multipart.

    """

    def __init__(self, file_path, multipart=None, chunk_size=None, upload_path=None):
        self.file_path = file_path
        self.upload_path = upload_path
        self.multipart = multipart
        if chunk_size is None:
            chunk_size = DEFAULT_UPLOAD_CHUNK_SIZE
        self.chunk_size = chunk_size


class MediaUpload:
    """

    Media Upload

    Arguments:

        file_path (str): Full path of the file to be uploaded
        
        upload_path (str): The URI path to be used for upload. Should be used in conjunction with the rootURL property at the API-level.
        
        mime_range (list): list of MIME Media Ranges for acceptable media uploads to this method.
        
        max_size (int): Maximum size of a media upload in bytes
        
        multipart (bool): True if this endpoint supports upload multipart media.

        chunksize (int): Size of a chunk of bytes that a session should read at a time when uploading in multipart.
        
        resumable (aiogoogle.models.ResumableUplaod): A ResumableUpload object

        validate (bool): Whether or not a session should validate the upload size before sending

    """

    def __init__(
        self,
        file_path,
        upload_path=None,
        mime_range=None,
        max_size=None,
        multipart=False,
        chunk_size=None,
        resumable=None,
        validate=True,
    ):
        self.file_path = file_path
        self.upload_path = upload_path
        self.mime_range = mime_range
        self.max_size = max_size
        self.multipart = multipart
        if chunk_size is None:
            chunk_size = DEFAULT_UPLOAD_CHUNK_SIZE
        self.chunk_size = chunk_size
        self.resumable = resumable
        self.validate = validate


class MediaDownload:
    """
    Media Download

    Arguments:

        file_path (str): Full path of the file to be downloaded

        chunksize (int): Size of a chunk of bytes that a session should write at a time when downloading.

    """

    def __init__(self, file_path, chunk_size=None):
        self.file_path = file_path
        if chunk_size is None:
            chunk_size = DEFAULT_DOWNLOAD_CHUNK_SIZE
        self.chunk_size = chunk_size


class Request:
    """
    Request class for the whole library. Auth Managers, GoogleAPI and Sessions should all use this.

    .. note::
        
        For HTTP body, only pass one of the following params:
            
            - json: json as a dict
            - data: www-url-form-encoded form as a dict/ bytes/ text/ 


    Parameters:

        method (str): HTTP method as a string (upper case) e.g. 'GET'
        
        url (str): full url as a string. e.g. 'https://example.com/api/v1/resource?filter=filter#something

        batch_url (str): full url of for sending this request in a batch
        
        json (dict): json as a dict
        
        data (any): www-url-form-encoded form as a dict/ bytes/ text/ 
        
        headers (dict): headers as a dict
        
        media_download (aiogoogle.models.MediaDownload): MediaDownload object
        
        media_upload (aiogoogle.models.MediaUpload): MediaUpload object
        
        timeout (int): Individual timeout for this request

        callback (callable): Synchronous callback that takes the content of the response as the only argument. Should also return content.

        _verify_ssl (boolean): Defaults to True.

        upload_file_content_type (str): Optional content-type header string. In case you don't want to use the default application/octet-stream (Or whatever is auto-detected by your transport handler)
        """

    def __init__(
        self,
        method=None,
        url=None,
        batch_url=None,
        headers=None,
        json=None,
        data=None,
        media_upload=None,
        media_download=None,
        timeout=None,
        callback=None,
        _verify_ssl=True,
        upload_file_content_type=None,
    ):
        self.method = method
        self.url = url
        self.batch_url = batch_url
        if headers is None:
            self.headers = {}
        else:
            self.headers = headers
        self.data = data
        self.json = json
        self.media_upload = media_upload
        self.media_download = media_download
        self.timeout = timeout
        self.callback = callback
        self._verify_ssl = _verify_ssl
        self.upload_file_content_type = upload_file_content_type

    def _add_query_param(self, query: dict):
        url = self.url
        if "?" not in url:
            if url.endswith("/"):
                url = url[:-1]
            url += "?"
        else:
            url += "&"
        query = urlencode(query)
        url += query
        self.url = url

    def _rm_query_param(self, name: str):
        u = urlparse(self.url)
        query = parse_qs(u.query)
        query.pop(name, None)
        u = u._replace(query=urlencode(query, True))
        self.url = urlunparse(u)

    @classmethod
    def batch_requests(cls, *requests):
        """
        Given many requests, will create a batch request per https://developers.google.com/discovery/v1/batch

        Arguments:

            *requests (aiogoogle.models.Request): Request objects

        Returns:

            aiogoogle.models.Request:
        """
        raise NotImplementedError

    @classmethod
    def from_response(cls, response):
        return Request(
            url=response.url,
            headers=response.headers,
            json=response.json,
            data=response.data,
        )


class Response:
    """
    Respnse Object

    Arguments:

        status_code (int): HTTP Status code

        headers (dict): HTTP response headers

        url (str): Request URL

        json (dict): Json Response if any

        data (any): data

        reason (str): reason for http error if any

        req (aiogoogle.models.Request): request that caused this response

        download_file (str): path of the download file specified in the request

        upload_file (str): path of the upload file specified in the request

        session_factory (aiogoogle.sessions.abc.AbstractSession): A callable implementation of aiogoogle's session interface
    """

    def __init__(
        self,
        status_code=None,
        headers=None,
        url=None,
        json=None,
        data=None,
        reason=None,
        req=None,
        download_file=None,
        upload_file=None,
        session_factory=None,
    ):
        if json and data:
            raise TypeError("Pass either json or data, not both.")

        self.status_code = status_code
        self.headers = headers
        self.url = url
        self.json = json
        self.data = data
        self.reason = reason
        self.req = req
        self.download_file = download_file
        self.upload_file = upload_file
        self.session_factory = session_factory

    @staticmethod
    async def _next_page_generator(
        prev_res,
        session_factory,
        req_token_name=None,
        res_token_name=None,
        json_req=False,
    ):
        prev_url = None
        while prev_res is not None:

            # Avoid infinite looping if google sent the same token twice
            if prev_url == prev_res.req.url:
                break
            prev_url = prev_res.req.url

            # yield
            yield prev_res.content

            # get request for next page
            next_req = prev_res.next_page(
                req_token_name=req_token_name,
                res_token_name=res_token_name,
                json_req=json_req,
            )
            if next_req is not None:
                async with session_factory() as sess:
                    prev_res = await sess.send(next_req, full_res=True)
            else:
                prev_res = None

    def __call__(
        self,
        session_factory=None,
        req_token_name=None,
        res_token_name=None,
        json_req=False,
    ):
        """
        Returns a generator that yields the contents of the next pages if any (and this page as well)

        Arguments:

            session_factory (aiogoogle.sessions.abc.AbstractSession): A session factory

            req_token_name (str):
            
                * name of the next_page token in the request

                * Default: "pageToken"
            
            res_token_name (str): 
            
                * name of the next_page token in json response

                * Default: "nextPageToken"

            json_req (dict): Normally, nextPageTokens should be sent in URL query params. If you want it in A json body, set this to True

        Returns:

            async generator: self._next_page_generator (staticmethod)
        """
        if session_factory is None:
            session_factory = self.session_factory
        return self._next_page_generator(
            self, session_factory, req_token_name, res_token_name, json_req
        )

    def __aiter__(self):
        return self._next_page_generator(self, self.session_factory)

    def __iter__(self):
        raise TypeError(
            'You probably forgot to use an "async for" statement instead of just a "for" statement.'
        )

    @property
    def content(self):
        """
        Equals either ``self.json`` or ``self.data``
        """
        return self.json or self.data

    def next_page(
        self, req_token_name=None, res_token_name=None, json_req=False
    ) -> Request:
        """
        Method that returns a request object that requests the next page of a resource

        Arguments:

            req_token_name (str):
            
                * name of the next_page token in the request

                * Default: "pageToken"
            
            res_token_name (str): 
            
                * name of the next_page token in json response

                * Default: "nextPageToken"

            json_req (dict): Normally, nextPageTokens should be sent in URL query params. If you want it in A json body, set this to True

        Returns:

            A request object (aiogoogle.models.Request):
        """
        if req_token_name is None:
            req_token_name = "pageToken"
        if res_token_name is None:
            res_token_name = "nextPageToken"
        res_token = self.json.get(res_token_name, None)
        if res_token == "":
            res_token = None
        if res_token is None:
            return None
        # request = Request.from_response(self)
        request = self.req
        if json_req:
            request.json[req_token_name] = res_token
        else:
            request._rm_query_param(req_token_name)
            request._add_query_param({req_token_name: res_token})
        return request

    @property
    def error_msg(self):
        if self.json is not None and self.json.get("error") is not None:
            return pprint.pformat(self.json["error"])

    def raise_for_status(self):
        if self.status_code >= 400:
            if self.error_msg is not None:
                self.reason = "\n\n" + self.reason + "\n\nContent:\n" + self.error_msg
            self.reason = "\n\n" + self.reason + "\n\nRequest URL:\n" + self.req.url
            if self.status_code == 401:
                raise AuthError(msg=self.reason, req=self.req, res=self)
            else:
                raise HTTPError(msg=self.reason, req=self.req, res=self)

    def __str__(self):
        return str(self.content)

    def __repr__(self):
        return f"Aiogoogle response model. Status: {str(self.status_code)}"
