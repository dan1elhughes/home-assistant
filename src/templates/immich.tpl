{# Immich template sensors and switches #}
- sensor:
{% for q in immich_queues %}
    - name: Immich {{ q.name }} Active
      unique_id: immich_{{ q.name | lower | replace(' ', '_') }}_active
      state: >-
        {% raw %}{{ state_attr('sensor.immich_{% endraw %}{{ q.name | lower | replace(' ', '_') }}{% raw %}_queued', 'jobCounts').active | int(0) }}{% endraw %}
    - name: Immich {{ q.name }} Completed
      unique_id: immich_{{ q.name | lower | replace(' ', '_') }}_completed
      unit_of_measurement: jobs
      state_class: total_increasing
      state: >-
        {% raw %}{{ state_attr('sensor.immich_{% endraw %}{{ q.name | lower | replace(' ', '_') }}{% raw %}_queued', 'jobCounts').completed | int(0) }}{% endraw %}
{% endfor %}

- switch:
{% for q in immich_queues %}
    - name: Immich {{ q.name }}
      unique_id: immich_{{ q.name | lower | replace(' ', '_') }}
      icon: {{ q.icon }}
      state: >-
        {% raw %}{{ not state_attr('sensor.immich_{% endraw %}{{ q.name | lower | replace(' ', '_') }}{% raw %}_queued', 'queueStatus').isPaused }}{% endraw %}
      turn_on:
        - service: rest_command.immich_resume_job
          data:
            job_name: {{ q.key }}
        - delay:
            seconds: 2
        - service: homeassistant.update_entity
          data:
            entity_id: sensor.immich_{{ q.name | lower | replace(' ', '_') }}_queued
      turn_off:
        - service: rest_command.immich_pause_job
          data:
            job_name: {{ q.key }}
        - delay:
            seconds: 2
        - service: homeassistant.update_entity
          data:
            entity_id: sensor.immich_{{ q.name | lower | replace(' ', '_') }}_queued
{% endfor %}
