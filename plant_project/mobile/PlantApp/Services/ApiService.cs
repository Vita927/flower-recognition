using System.Net.Http.Headers;
using System.Text.Json;
using PlantApp.Models;

namespace PlantApp.Services;

/// <summary>Ошибка, пришедшая от сервера (или проблема связи).</summary>
public class ApiException : Exception
{
    public int StatusCode { get; }
    public string Code { get; }

    public ApiException(int statusCode, string code, string message) : base(message)
    {
        StatusCode = statusCode;
        Code = code;
    }
}

public class ApiService
{
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromSeconds(30) };

    // Эмулятор Android видит ПК по 10.0.2.2. Для телефона введите IP из консоли сервера.
    private string _baseUrl = "http://10.0.2.2:8000";

    public string BaseUrl => _baseUrl;

    public void SetBaseUrl(string url) => _baseUrl = url.Trim().TrimEnd('/');

    public async Task<HealthResponse> CheckHealthAsync(CancellationToken ct = default)
        => await GetAsync<HealthResponse>("/health", ct);

    public async Task<ClassesResponse> GetClassesAsync(CancellationToken ct = default)
        => await GetAsync<ClassesResponse>("/classes", ct);

    /// <summary>Отправить фото на распознавание.</summary>
    public async Task<PredictResponse> PredictAsync(
        Stream image, string fileName = "photo.jpg", int topK = 5, CancellationToken ct = default)
    {
        using var content = new MultipartFormDataContent();
        var file = new StreamContent(image);
        file.Headers.ContentType = new MediaTypeHeaderValue("image/jpeg");
        content.Add(file, "file", fileName); // имя поля "file" — по контракту

        try
        {
            using var response = await _http.PostAsync($"{_baseUrl}/predict?top_k={topK}", content, ct);
            return await ReadAsync<PredictResponse>(response, ct);
        }
        catch (Exception ex) when (ex is HttpRequestException or TaskCanceledException)
        {
            throw new ApiException(0, "network_error",
                "Не удалось связаться с сервером. Проверьте адрес и Wi-Fi.");
        }
    }

    private async Task<T> GetAsync<T>(string path, CancellationToken ct)
    {
        try
        {
            using var response = await _http.GetAsync($"{_baseUrl}{path}", ct);
            return await ReadAsync<T>(response, ct);
        }
        catch (Exception ex) when (ex is HttpRequestException or TaskCanceledException)
        {
            throw new ApiException(0, "network_error",
                "Не удалось связаться с сервером. Проверьте адрес и Wi-Fi.");
        }
    }

    private static async Task<T> ReadAsync<T>(HttpResponseMessage response, CancellationToken ct)
    {
        var body = await response.Content.ReadAsStringAsync(ct);

        if (!response.IsSuccessStatusCode)
        {
            ErrorResponse? err = null;
            try { err = JsonSerializer.Deserialize<ErrorResponse>(body); } catch { /* не JSON */ }
            throw new ApiException(
                (int)response.StatusCode,
                err?.Error?.Code ?? "unknown",
                err?.Error?.Message ?? $"Ошибка сервера ({(int)response.StatusCode})");
        }

        return JsonSerializer.Deserialize<T>(body)
               ?? throw new ApiException((int)response.StatusCode, "bad_response", "Пустой ответ сервера");
    }
}
