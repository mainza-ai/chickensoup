import SwiftUI

struct WikiBrowserView: View {
    @ObservedObject var backendService = BackendService.shared

    @State private var searchText = ""
    @State private var selectedType: String? = nil
    @State private var showDeleteConfirmation = false
    @State private var pageToDelete: APIWikiPageListItem? = nil
    @State private var deleteResult: APIWikiDeleteResponse? = nil
    @State private var selectedPage: APIWikiPageDetail? = nil
    @State private var showPageDetail = false

    private var filteredPages: [APIWikiPageListItem] {
        var pages = backendService.wikiPages
        if let type = selectedType {
            pages = pages.filter { $0.pageType == type }
        }
        if !searchText.isEmpty {
            let q = searchText.lowercased()
            pages = pages.filter { $0.title.lowercased().contains(q) || $0.tags.contains { $0.lowercased().contains(q) } }
        }
        return pages
    }

    var body: some View {
        VStack(spacing: 0) {
            if let error = backendService.wikiPagesError {
                HStack(spacing: 8) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundStyle(DesignConstants.systemRed)
                    Text("Error loading wiki: \(error)")
                        .font(.caption)
                        .foregroundStyle(DesignConstants.systemRed)
                    Spacer()
                    Button("Retry") {
                        Task { await backendService.fetchWikiPages() }
                    }
                    .font(.caption)
                    .buttonStyle(.bordered)
                    .tint(DesignConstants.systemRed)
                }
                .padding(.horizontal, DesignConstants.standardPadding)
                .padding(.vertical, 8)
                .background(DesignConstants.systemRed.opacity(0.1))
            }
            filterBar
            Divider()
            if backendService.isFetchingWikiPages && backendService.wikiPages.isEmpty {
                Spacer()
                ProgressView("Loading wiki pages...")
                Spacer()
            } else if filteredPages.isEmpty {
                Spacer()
                VStack(spacing: 8) {
                    Image(systemName: "book.closed")
                        .font(.largeTitle)
                        .foregroundStyle(DesignConstants.secondaryText)
                    Text("No wiki pages found")
                        .font(.subheadline)
                        .foregroundStyle(DesignConstants.secondaryText)
                }
                Spacer()
            } else {
                List {
                    ForEach(filteredPages) { page in
                        Button {
                            Task {
                                let detail = await backendService.fetchWikiPageDetail(slug: page.slug, pageType: page.pageType)
                                if let detail = detail {
                                    selectedPage = detail
                                    showPageDetail = true
                                }
                            }
                        } label: {
                            WikiPageRow(page: page)
                        }
                        .buttonStyle(.plain)
                        .swipeActions(edge: .trailing, allowsFullSwipe: false) {
                            if !page.protected {
                                Button("Delete", role: .destructive) {
                                    pageToDelete = page
                                    showDeleteConfirmation = true
                                }
                            }
                        }
                    }
                }
                .listStyle(.plain)
                .refreshable {
                    await backendService.fetchWikiPages()
                }
            }
        }
        .navigationTitle("Wiki Pages")
        .task {
            await backendService.fetchWikiPages()
        }
        .sheet(isPresented: $showPageDetail) {
            if let detail = selectedPage {
                NavigationStack {
                    WikiPageDetailView(detail: detail)
                }
            }
        }
        .alert("Delete Wiki Entry", isPresented: $showDeleteConfirmation, presenting: pageToDelete) { page in
            Button("Cancel", role: .cancel) {
                pageToDelete = nil
            }
            Button("Delete", role: .destructive) {
                Task {
                    let result = await backendService.deleteWikiPage(slug: page.slug, pageType: page.pageType, hard: true)
                    deleteResult = result
                    await backendService.fetchWikiPages()
                }
            }
        } message: { page in
            Text("Delete '\(page.title)'? This removes the page from disk and Neo4j graph. Cross-references will be cleaned up.")
        }
    }

    private var filterBar: some View {
        HStack(spacing: 8) {
            Image(systemName: "magnifyingglass")
                .foregroundStyle(DesignConstants.secondaryText)
            TextField("Search by title or tag...", text: $searchText)
                .textFieldStyle(.plain)
                .font(.subheadline)
            Spacer()
            typeFilterButton("All", type: nil)
            typeFilterButton("Entities", type: "entities")
            typeFilterButton("Concepts", type: "concepts")
            typeFilterButton("Projects", type: "projects")
        }
        .padding(.horizontal, DesignConstants.standardPadding)
        .padding(.vertical, 8)
    }

    private func typeFilterButton(_ label: String, type: String?) -> some View {
        Button(label) {
            selectedType = selectedType == type ? nil : type
        }
        .font(.caption2)
        .fontWeight(.bold)
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(selectedType == type ? DesignConstants.systemBlue.opacity(0.2) : Color.clear)
        .foregroundStyle(selectedType == type ? DesignConstants.systemBlue : DesignConstants.secondaryText)
        .clipShape(Capsule())
        .overlay(
            Capsule()
                .stroke(selectedType == type ? DesignConstants.systemBlue.opacity(0.4) : DesignConstants.dividerColor, lineWidth: 1)
        )
    }
}

struct WikiPageRow: View {
    let page: APIWikiPageListItem

    var body: some View {
        HStack(spacing: 12) {
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 6) {
                    Text(page.title)
                        .font(.body)
                        .fontWeight(.bold)
                        .foregroundStyle(DesignConstants.primaryText)
                    if page.protected {
                        Image(systemName: "lock.fill")
                            .font(.caption2)
                            .foregroundStyle(DesignConstants.systemOrange)
                    }
                }
                if !page.tags.isEmpty {
                    Text(page.tags.prefix(3).joined(separator: ", "))
                        .font(.caption2)
                        .foregroundStyle(DesignConstants.secondaryText)
                        .lineLimit(1)
                }
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 4) {
                Text(page.pageType.capitalized)
                    .font(.caption2)
                    .fontWeight(.bold)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(typeColor(page.pageType).opacity(0.15))
                    .foregroundStyle(typeColor(page.pageType))
                    .clipShape(Capsule())
                if !page.updated.isEmpty {
                    Text(page.updated)
                        .font(.caption2)
                        .foregroundStyle(DesignConstants.secondaryText)
                }
            }
        }
        .padding(.vertical, 4)
    }

    private func typeColor(_ type: String) -> Color {
        switch type {
        case "entities": return DesignConstants.systemBlue
        case "concepts": return DesignConstants.systemPurple
        case "projects": return DesignConstants.systemGreenText
        default: return DesignConstants.secondaryText
        }
    }
}
