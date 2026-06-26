import Foundation
import SwiftUI

@MainActor @Observable
public final class WikiService {
    public static let shared = WikiService()

    public var wikiPages: [APIWikiPageListItem] = []
    public var isFetchingWikiPages = false
    public var isDeletingWikiPage = false
    public var wikiPagesError: String? = nil

    public var isClearingWiki = false
    public var isExportingWiki = false

    private init() {}

    // MARK: - List Pages

    public func fetchWikiPages(pageType: String? = nil) async {
        isFetchingWikiPages = true
        defer { isFetchingWikiPages = false }
        do {
            let queryItems: [URLQueryItem]? = pageType.map { [URLQueryItem(name: "page_type", value: $0)] }
            let response: APIWikiPageListResponse = try await APIClient.shared.request(
                path: "/wiki/pages", queryItems: queryItems
            )
            self.wikiPages = response.pages
            self.wikiPagesError = nil
        } catch {
            self.wikiPagesError = error.localizedDescription
            print("Failed to fetch wiki pages: \(error.localizedDescription)")
        }
    }

    // MARK: - Page Detail

    public func fetchWikiPageDetail(slug: String, pageType: String) async -> APIWikiPageDetail? {
        do {
            let response: APIWikiPageDetail = try await APIClient.shared.request(
                path: "/wiki/page/\(slug)",
                queryItems: [URLQueryItem(name: "page_type", value: pageType)]
            )
            return response
        } catch {
            print("Failed to fetch wiki page detail: \(error.localizedDescription)")
            return nil
        }
    }

    // MARK: - Delete Page

    @discardableResult
    public func deleteWikiPage(slug: String, pageType: String, hard: Bool = false) async -> APIWikiDeleteResponse? {
        isDeletingWikiPage = true
        defer { isDeletingWikiPage = false }
        do {
            var queryItems = [URLQueryItem(name: "page_type", value: pageType)]
            if hard { queryItems.append(URLQueryItem(name: "hard", value: "true")) }
            let bodyData = try JSONSerialization.data(withJSONObject: [:])
            let response: APIWikiDeleteResponse = try await APIClient.shared.request(
                path: "/wiki/page/\(slug)", method: "DELETE", body: bodyData, queryItems: queryItems
            )
            return response
        } catch {
            print("Failed to delete wiki page: \(error.localizedDescription)")
            return nil
        }
    }

    // MARK: - Clear / Export / Import

    public func clearWikiContent() async -> APIWikiClearResponse? {
        isClearingWiki = true
        defer { isClearingWiki = false }
        do {
            let bodyData = try JSONSerialization.data(withJSONObject: [:])
            let response: APIWikiClearResponse = try await APIClient.shared.request(
                path: "/wiki/clear-content", method: "POST", body: bodyData
            )
            return response
        } catch {
            print("Failed to clear wiki content: \(error.localizedDescription)")
            return nil
        }
    }

    public func exportWiki() async -> APIWikiExportResponse? {
        isExportingWiki = true
        defer { isExportingWiki = false }
        do {
            let response: APIWikiExportResponse = try await APIClient.shared.request(path: "/wiki/export")
            return response
        } catch {
            print("Failed to export wiki: \(error.localizedDescription)")
            return nil
        }
    }

    public func importWiki(fileURL: URL) async -> APIWikiImportResponse? {
        defer { try? FileManager.default.removeItem(at: fileURL) }
        do {
            let fileData = try Data(contentsOf: fileURL)
            return try await APIClient.shared.uploadMultipart(
                path: "/wiki/import",
                fileData: fileData,
                filename: "wiki-import.zip",
                contentType: "application/zip"
            ) as APIWikiImportResponse
        } catch {
            print("Failed to import wiki: \(error.localizedDescription)")
            return nil
        }
    }
}
