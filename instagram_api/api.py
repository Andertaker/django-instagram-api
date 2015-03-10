from django.conf import settings
from oauth_tokens.models import AccessToken

from instagram.client import InstagramAPI
from oauth_tokens.api import ApiAbstractBase, Singleton


__all__ = ['get_api', ]

INSTAGRAM_CLIENT_ID = getattr(settings, 'OAUTH_TOKENS_INSTAGRAM_CLIENT_ID', None)
INSTAGRAM_CLIENT_SECRET = getattr(settings, 'OAUTH_TOKENS_INSTAGRAM_CLIENT_SECRET', None)

INSTAGRAM_API_ACCESS_TOKEN = getattr(settings, 'INSTAGRAM_API_ACCESS_TOKEN', None)



class InstagramToken(ApiAbstractBase):

    __metaclass__ = Singleton

    provider = 'instagram'
    #error_class = TwitterError

    #def get_consistent_token(self):
    #    return getattr(settings, 'INSTAGRAM_API_ACCESS_TOKEN', None)

    #def get_tokens(self, **kwargs):
    #    return AccessToken.objects.filter_active_tokens_of_provider(self.provider, **kwargs)


    def get_api(self, **kwargs):
        token = self.get_token(**kwargs)

        return InstagramAPI(access_token=token)

    def get_api_response(self, *args, **kwargs):
        return getattr(self.api, self.method)(*args, **kwargs)

    def get_error_code(self, e):
        e.code = e[0][0]['code'] if 'code' in e[0][0] else 0

    def handle_error_no_active_tokens(self, e, *args, **kwargs):
        if self.used_access_tokens and self.api:

            # check if all tokens are blocked by rate limits response
            try:
                rate_limit_status = self.api.rate_limit_status()
            except self.error_class, e:
                self.get_error_code(e)
                # handle rate limit on rate_limit_status request -> wait 15 min and repeat main request
                if e.code == 88:
                    self.used_access_tokens = []
                    return self.sleep_repeat_call(seconds=60 * 15, *args, **kwargs)
                else:
                    raise

            # TODO: wrong logic, path is different completelly sometimes
            method = '/%s' % self.method.replace('_', '/')
            status = [methods for methods in rate_limit_status['resources'].values() if method in methods][0][method]
            if status['remaining'] == 0:
                secs = (datetime.fromtimestamp(status['reset']) - datetime.now()).seconds
                self.used_access_tokens = []
                return self.sleep_repeat_call(seconds=secs, *args, **kwargs)
            else:
                return self.repeat_call(*args, **kwargs)
        else:
            return super(InstagramToken, self).handle_error_no_active_tokens(e, *args, **kwargs)

    def handle_error_code(self, e, *args, **kwargs):
        self.get_error_code(e)
        return super(InstagramToken, self).handle_error_code(e, *args, **kwargs)

    def handle_error_code_88(self, e, *args, **kwargs):
        # Rate limit exceeded
        token = AccessToken.objects.get_token_class(self.provider).delimeter.join(
            [self.api.auth.access_token, self.api.auth.access_token_secret])
        self.used_access_tokens += [token]
        return self.repeat_call(*args, **kwargs)

#     def handle_error_code_63(self, e, *args, **kwargs):
# User has been suspended.
#         self.refresh_tokens()
#         return self.repeat_call(*args, **kwargs







def get_api(*args, **kwargs):
    #api = InstagramAPI(client_id=INSTAGRAM_CLIENT_ID, client_secret=INSTAGRAM_CLIENT_SECRET)
    #return api.call(*args, **kwargs)
    #print "___________________"
    #it = InstagramToken()
    #token = it.get_token()
    #print "token: ", token

    api = InstagramAPI(access_token=INSTAGRAM_API_ACCESS_TOKEN)

    return api
