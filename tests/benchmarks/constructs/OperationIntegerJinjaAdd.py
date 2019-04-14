{% extends "layout" %}
{% block start %}
module_value1 = 5000
module_value2 = 3000
{% endblock %}

{% block in_function %}
    module_value1

    local_value = module_value1

    s = module_value1
    t = module_value2
{% endblock %}
{% block construct %}
    t = s + t
{% endblock %}
