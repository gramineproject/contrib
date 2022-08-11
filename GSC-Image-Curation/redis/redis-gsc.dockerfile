From redis

# COPY ca.crt /ca.crt

# These two lines are required in order to incorporate runtime args with the image entrypoint and cmd
COPY entry_script_redis.sh /usr/local/bin/entry_script_redis.sh
ENTRYPOINT ["/bin/bash", "/usr/local/bin/entry_script_redis.sh"]
