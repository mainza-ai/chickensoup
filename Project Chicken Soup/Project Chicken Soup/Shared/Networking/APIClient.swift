//
//  APIClient.swift
//  Project Chicken Soup
//
//  Created by mck on 6/23/26.
//

import Foundation

public enum APIError: Error, LocalizedError {
    case invalidURL
    case requestFailed(Error)
    case invalidResponse
    case httpError(statusCode: Int)
    case decodingFailed(Error)
    
    public var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "The request URL is invalid."
        case .requestFailed(let error):
            return "The network request failed: \(error.localizedDescription)"
        case .invalidResponse:
            return "The server returned an invalid response."
        case .httpError(let statusCode):
            return "The server returned an HTTP error code \(statusCode)."
        case .decodingFailed(let error):
            return "Failed to decode the response: \(error.localizedDescription)"
        }
    }
}

public actor APIClient {
    public static let shared = APIClient()

    private let session: URLSession
    public private(set) var baseURL: URL
    public private(set) var apiKey: String = ""

    public init(baseURL: URL = URL(string: "http://127.0.0.1:8000")!) {
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = 30.0
        self.session = URLSession(configuration: configuration)
        self.baseURL = baseURL
    }

    public func updateBaseURL(_ url: URL) {
        self.baseURL = url
    }

    public func updateAPIKey(_ key: String) {
        self.apiKey = key
    }

    public func request<T: Decodable>(
        path: String,
        method: String = "GET",
        body: Data? = nil,
        queryItems: [URLQueryItem]? = nil
    ) async throws -> T {
        try await requestWithRetry(path: path, method: method, body: body, queryItems: queryItems, retries: 2)
    }

    private func requestWithRetry<T: Decodable>(
        path: String,
        method: String = "GET",
        body: Data? = nil,
        queryItems: [URLQueryItem]? = nil,
        retries: Int
    ) async throws -> T {
        var urlComponents = URLComponents(url: baseURL.appendingPathComponent(path), resolvingAgainstBaseURL: true)
        if let queryItems = queryItems {
            urlComponents?.queryItems = queryItems
        }

        guard let url = urlComponents?.url else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if !apiKey.isEmpty {
            request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        }
        request.httpBody = body

        let data: Data
        let response: URLResponse

        do {
            (data, response) = try await session.data(for: request)
        } catch {
            if retries > 0, isTransientError(error) {
                try await Task.sleep(for: .seconds(1.0))
                return try await requestWithRetry(path: path, method: method, body: body, queryItems: queryItems, retries: retries - 1)
            }
            throw APIError.requestFailed(error)
        }

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            if retries > 0, isRetryableStatusCode(httpResponse.statusCode) {
                try await Task.sleep(for: .seconds(1.0))
                return try await requestWithRetry(path: path, method: method, body: body, queryItems: queryItems, retries: retries - 1)
            }
            throw APIError.httpError(statusCode: httpResponse.statusCode)
        }

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let dateStr = try container.decode(String.self)

            let dateFormatter = ISO8601DateFormatter()
            if let date = dateFormatter.date(from: dateStr) {
                return date
            }

            let fractionalFormatter = ISO8601DateFormatter()
            fractionalFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            if let date = fractionalFormatter.date(from: dateStr) {
                return date
            }

            if let doubleVal = Double(dateStr) {
                return Date(timeIntervalSince1970: doubleVal)
            }
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Cannot decode date string \(dateStr)")
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingFailed(error)
        }
    }

    private func isTransientError(_ error: Error) -> Bool {
        let nsError = error as NSError
        let transientCodes: Set<URLError.Code> = [
            .timedOut, .networkConnectionLost, .notConnectedToInternet,
            .dnsLookupFailed, .secureConnectionFailed, .cannotConnectToHost
        ]
        if let urlError = error as? URLError, transientCodes.contains(urlError.code) {
            return true
        }
        return nsError.domain == NSURLErrorDomain
    }

    private func isRetryableStatusCode(_ code: Int) -> Bool {
        [429, 502, 503, 504].contains(code)
    }

    // MARK: - Multipart Upload

    public func uploadMultipart<T: Decodable>(
        path: String,
        fileData: Data,
        filename: String,
        contentType: String = "application/octet-stream",
        method: String = "POST"
    ) async throws -> T {
        let boundary = UUID().uuidString
        var request = URLRequest(url: baseURL.appendingPathComponent(path))
        request.httpMethod = method
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        if !apiKey.isEmpty {
            request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        }

        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: \(contentType)\r\n\r\n".data(using: .utf8)!)
        body.append(fileData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        request.httpBody = body

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse, (200...299).contains(httpResponse.statusCode) else {
            let statusCode = (response as? HTTPURLResponse)?.statusCode ?? -1
            throw APIError.httpError(statusCode: statusCode)
        }

        do {
            return try JSONDecoder().decode(T.self, from: data)
        } catch {
            throw APIError.decodingFailed(error)
        }
    }
}
