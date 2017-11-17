#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64


def decodeUrl(url):
    '''
    针对中国大陆的网络, url 要加密两次才不会被 gfw 发现, 这里也要解密两次
    >>> decodeUrl('YUhSMGNEb3ZMelk0TG0xbFpHbGhMblIxYldKc2NpNWpiMjB2TVRNNFpUZzBPV0ZsWWpkbE4yUmhPV1ppT1dGaVpXUTFOamxsT0dVMU9ETXZkSFZ0WW14eVgyNXBOV0o1Y1VObVNFWXhkSE0zZFRCeWJ6UmZjakZmTVRJNE1DNXFjR2M9')
    b'http://68.media.tumblr.com/138e849aeb7e7da9fb9abed569e8e583/tumblr_ni5byqCfHF1ts7u0ro4_r1_1280.jpg'
    '''
    return base64.b64decode(base64.b64decode(url))


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
