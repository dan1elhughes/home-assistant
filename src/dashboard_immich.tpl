views:
  - type: sections
    max_columns: 4
    title: Immich
    path: immich
    icon: mdi:image-multiple
    sections:
{% for q in immich_queues %}
      - type: grid
        title: {{ q.name }}
        cards:
          - type: tile
            entity: switch.immich_{{ q.name | lower | replace(' ', '_') }}
            name: Active
            vertical: false
          - type: tile
            entity: sensor.immich_{{ q.name | lower | replace(' ', '_') }}_rate_per_hour
            name: Rate
            vertical: false
          - type: tile
            entity: sensor.immich_{{ q.name | lower | replace(' ', '_') }}_queued
            name: Queue
            vertical: false
            features:
              - type: trend-graph
            features_position: inline
            grid_options:
              columns: full
{% endfor %}
