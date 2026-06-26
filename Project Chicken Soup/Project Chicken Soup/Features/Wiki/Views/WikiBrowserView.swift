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
        List {
            if backendService.isFetchingWikiPages && backendService.wikiPages.isEmpty {
                Section {
                    HStack {
                        Spacer()
                        ProgressView("Loading wiki pages...")
                        Spacer()
                    }
                    .listRowBackground(Color.clear)
                }
            } else if backendService.wikiPagesError != nil {
                Section {
                    HStack(spacing: 8) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundStyle(DesignConstants.systemRed)
                        Text(backendService.wikiPagesError!)
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
                    .listRowBackground(Color.clear)
                }
            } else if filteredPages.isEmpty {
                Section {
                    HStack {
                        Spacer()
                        VStack(spacing: 8) {
                            Image(systemName: "book.closed")
                                .font(.largeTitle)
                                .foregroundStyle(DesignConstants.secondaryText)
                            Text("No wiki pages found")
                                .font(.subheadline)
                                .foregroundStyle(DesignConstants.secondaryText)
                                .padding(.top, 4)
                        }
                        Spacer()
                    }
                    .listRowBackground(Color.clear)
                }
            } else {
                Section {
                    ForEach(filteredPages) { page in
                        NavigationLink {
                            WikiPageDetailView(loader: WikiPageLoader(slug: page.slug, pageType: page.pageType))
                        } label: {
                            WikiPageRow(page: page)
                        }
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
            }
        }
        .listStyle(.plain)
        #if os(macOS)
        .searchable(text: $searchText, prompt: "Search by title or tag...")
        #else
        .searchable(text: $searchText, placement: .navigationBarDrawer(displayMode: .always), prompt: "Search by title or tag...")
        #endif
        .navigationTitle("Wiki Pages (\(filteredPages.count))")
        .task {
            await backendService.fetchWikiPages()
        }
        .refreshable {
            await backendService.fetchWikiPages()
        }
        .toolbar {
            ToolbarItem(placement: .principal) {
                Picker("Type", selection: $selectedType) {
                    Text("All").tag(nil as String?)
                    Text("Entities").tag("entities" as String?)
                    Text("Concepts").tag("concepts" as String?)
                    Text("Projects").tag("projects" as String?)
                }
                .pickerStyle(.segmented)
                .frame(maxWidth: 320)
            }
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

// MARK: - Wiki Page Loader (async detail fetch)

@Observable
@MainActor
class WikiPageLoader {
    var detail: APIWikiPageDetail? = nil
    var isLoading = false
    var error: String? = nil

    let slug: String
    let pageType: String

    init(slug: String, pageType: String) {
        self.slug = slug
        self.pageType = pageType
    }

    func load() async {
        isLoading = true
        let result = await BackendService.shared.fetchWikiPageDetail(slug: slug, pageType: pageType)
        isLoading = false
        if let detail = result {
            self.detail = detail
        } else {
            self.error = "Failed to load page detail"
        }
    }
}
