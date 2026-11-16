using System.Text.Json.Serialization;

namespace PlantApp.Models;

// Модели повторяют JSON из API_CONTRACT.md (версия 1.0).

public class HealthResponse
{
    [JsonPropertyName("status")] public string Status { get; set; } = "";
    [JsonPropertyName("model_loaded")] public bool ModelLoaded { get; set; }
    [JsonPropertyName("api_version")] public string ApiVersion { get; set; } = "";
    [JsonPropertyName("model_version")] public string ModelVersion { get; set; } = "";
}

public class ClassInfo
{
    [JsonPropertyName("id")] public int Id { get; set; }
    [JsonPropertyName("label")] public string Label { get; set; } = "";
    [JsonPropertyName("name_ru")] public string NameRu { get; set; } = "";
}

public class ClassesResponse
{
    [JsonPropertyName("count")] public int Count { get; set; }
    [JsonPropertyName("classes")] public List<ClassInfo> Classes { get; set; } = new();
}

public class Prediction
{
    [JsonPropertyName("class_id")] public int ClassId { get; set; }
    [JsonPropertyName("label")] public string Label { get; set; } = "";
    [JsonPropertyName("name_ru")] public string NameRu { get; set; } = "";
    [JsonPropertyName("confidence")] public double Confidence { get; set; }

    // Для интерфейса: "91 %" и значение для ProgressBar (0..1)
    [JsonIgnore] public string ConfidenceText => $"{Confidence * 100:0} %";
}

public class PredictResponse
{
    [JsonPropertyName("predictions")] public List<Prediction> Predictions { get; set; } = new();
    [JsonPropertyName("inference_ms")] public int InferenceMs { get; set; }
    [JsonPropertyName("model_version")] public string ModelVersion { get; set; } = "";
}

// Формат ошибки: { "error": { "code": "...", "message": "..." } }
public class ErrorResponse
{
    [JsonPropertyName("error")] public ErrorBody? Error { get; set; }
}

public class ErrorBody
{
    [JsonPropertyName("code")] public string Code { get; set; } = "";
    [JsonPropertyName("message")] public string Message { get; set; } = "";
}
