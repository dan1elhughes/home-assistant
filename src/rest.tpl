# Immich job queue monitoring
- scan_interval: 60
  resource: https://photos.danhughes.dev/api/jobs
  headers:
    x-api-key: !secret immich_api_key_queue_management
  sensor:
{% for q in immich_queues %}
    - name: Immich {{ q.name }} Queued
      unique_id: immich_{{ q.name | lower | replace(' ', '_') }}_queued
      icon: {{ q.icon }}
      unit_of_measurement: jobs
      value_template: >-
        {% raw %}{{ value_json.{% endraw %}{{ q.key }}{% raw %}.jobCounts.waiting
           + value_json.{% endraw %}{{ q.key }}{% raw %}.jobCounts.paused }}{% endraw %}
      json_attributes_path: $.{{ q.key }}
      json_attributes:
        - queueStatus
        - jobCounts
{% endfor %}
