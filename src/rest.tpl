# AgilePredict export price forecasts for region J (South Eastern England)
- scan_interval: 3600
  resource: https://agilepredict.com/api/J/?days=14&forecast_count=1&export=true
  sensor:
    - name: Agile Predict Export
      unique_id: agile_predict_export_region_j
      icon: mdi:flash
      value_template: >-
        {% raw %}{{ value_json[0]['name'] }}{% endraw %}
      json_attributes_path: "$[0]"
      json_attributes:
        - created_at
        - prices

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
