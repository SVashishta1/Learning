{{/*
_helpers.tpl: small reusable pieces ("named templates"). Files starting with "_" create no
Kubernetes objects. Other templates use them with:  {{ include "hello-ai.fullname" . }}
*/}}

{{/* The name of every object: "<release name>-<chart name>", e.g. "hello-hello-ai". */}}
{{- define "hello-ai.fullname" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/* Labels used to SELECT the pods. They must never change after install. */}}
{{- define "hello-ai.selectorLabels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/* All labels: the selector labels plus some useful information. */}}
{{- define "hello-ai.labels" -}}
{{ include "hello-ai.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end -}}
