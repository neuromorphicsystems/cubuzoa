import re

regex = re.compile('^(\d[\.\d]*(?<= \d))((?:[abc]|rc)\d+)?(?:(\.post\d+))?(?:(\.dev\d+))?(?:(\+(?![.])[a-zA-Z0-9\.]*[a-zA-Z0-9]))?$')
