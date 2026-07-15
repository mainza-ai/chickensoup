import SwiftUI
import SwiftData

struct WikiBrowserView: View {
    var backendService = BackendService.shared
    @Environment(\.modelContext) private var modelContext

    @State private var searchText = ""
    @State private var debouncedSearchText = ""
    @State private var searchResults: [APISearchResult] = []
    @State private var isSearching = false
    @State private var selectedType: String? = nil
    @State private var showDeleteConfirmation = false
    @State private var pageToDelete: APIWikiPageListItem? = nil
    @State private var selectedPage: APIWikiPageListItem? = nil

    private var filteredPages: [APIWikiPageListItem] {
        var pages = backendService.wiki.wikiPages
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
        List(selection: $selectedPage) {
            if isSearching {
                HStack { Spacer(); ProgressView("Searching..."); Spacer() }
                    .listRowBackground(Color.clear)
            } else if !debouncedSearchText.isEmpty {
                if searchResults.isEmpty {
                    emptySearchSection
                } else {
                    Section {
                        ForEach(searchResults) { result in
                            SearchResultRow(result: result)
                        }
                    }
                }
            } else if backendService.wiki.isFetchingWikiPages && backendService.wiki.wikiPages.isEmpty {
                ProgressView("Loading wiki pages...")
                    .frame(maxWidth: .infinity)
                    .listRowBackground(Color.clear)
            } else if let error = backendService.wiki.wikiPagesError {
                errorSection(error)
            } else if filteredPages.isEmpty {
                emptySection
            } else {
                Section {
                    ForEach(filteredPages) { page in
                        WikiPageCell(page: page, onDelete: {
                            pageToDelete = page
                            showDeleteConfirmation = true
                        })
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
        .navigationTitle("Wiki Pages" + (debouncedSearchText.isEmpty ? " (\(filteredPages.count))" : ""))
        .navigationDestination(for: APIWikiPageListItem.self) { page in
            WikiPageDetailView(loader: WikiPageLoader(slug: page.slug, pageType: page.pageType))
        }
        .task {
            await backendService.wiki.fetchWikiPages()
        }
        .refreshable {
            await backendService.wiki.fetchWikiPages()
        }
        .onChange(of: searchText) { _, newValue in
            Task {
                try? await Task.sleep(for: .milliseconds(300))
                if newValue == searchText {
                    debouncedSearchText = newValue
                    if !newValue.isEmpty {
                        await performSearch(newValue)
                    } else {
                        searchResults = []
                    }
                }
            }
        }
        .toolbar { toolbarContent }
        #if os(macOS)
        .onDeleteCommand {
            if let page = selectedPage, !page.protected {
                pageToDelete = page
                showDeleteConfirmation = true
            }
        }
        #endif
        .alert("Delete Wiki Entry", isPresented: $showDeleteConfirmation, presenting: pageToDelete) { page in
            Button("Cancel", role: .cancel) { pageToDelete = nil }
            Button("Delete", role: .destructive) {
                Task {
                    await backendService.deleteWikiPage(slug: page.slug, pageType: page.pageType, hard: true)
                    await backendService.wiki.fetchWikiPages()
                    await backendService.fetchLoreEntities(context: modelContext)
                    await backendService.fetchTemporalEvents(context: modelContext)
                }
            }
        } message: { page in
            Text("Delete '\(page.title)'? This removes the page from disk and Neo4j graph. Cross-references will be cleaned up.")
        }
    }

    private func performSearch(_ query: String) async {
        isSearching = true
        defer { isSearching = false }
        if let response = await backendService.performSearch(query: query, limit: 25) {
            searchResults = response.results
        }
    }

    @ToolbarContentBuilder
    private var toolbarContent: some ToolbarContent {
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
        #if os(macOS)
        ToolbarItem {
            Button("Refresh", systemImage: "arrow.clockwise") {
                Task {
                    await backendService.wiki.fetchWikiPages()
                    await backendService.fetchLoreEntities(context: modelContext)
                    await backendService.fetchTemporalEvents(context: modelContext)
                }
            }
            .keyboardShortcut("r")
        }
        ToolbarItem {
            Button("Delete", systemImage: "trash") {
                if let page = selectedPage, !page.protected {
                    pageToDelete = page
                    showDeleteConfirmation = true
                }
            }
            .disabled(selectedPage == nil || selectedPage!.protected)
        }
        #endif
    }

    private var emptySearchSection: some View {
        Section {
            HStack {
                Spacer()
                VStack(spacing: 8) {
                    Image(systemName: "magnifyingglass").font(.largeTitle).foregroundStyle(DesignConstants.secondaryText)
                    Text("No results found").font(.subheadline).foregroundStyle(DesignConstants.secondaryText)
                }
                Spacer()
            }
            .listRowBackground(Color.clear)
        }
    }

    private var emptySection: some View {
        Section {
            HStack {
                Spacer()
                VStack(spacing: 8) {
                    Image(systemName: "book.closed").font(.largeTitle).foregroundStyle(DesignConstants.secondaryText)
                    Text("No wiki pages found").font(.subheadline).foregroundStyle(DesignConstants.secondaryText).padding(.top, 4)
                }
                Spacer()
            }
            .listRowBackground(Color.clear)
        }
    }

    func errorSection(_ error: String) -> some View {
        Section {
            HStack(spacing: 8) {
                Image(systemName: "exclamationmark.triangle.fill").foregroundStyle(DesignConstants.systemRed)
                Text(error).font(.caption).foregroundStyle(DesignConstants.systemRed)
                Spacer()
                Button("Retry") { Task { await backendService.wiki.fetchWikiPages() } }
                    .font(.caption).buttonStyle(.bordered).tint(DesignConstants.systemRed)
            }
            .listRowBackground(Color.clear)
        }
    }
}

struct SearchResultRow: View {
    let result: APISearchResult

    var body: some View {
        NavigationLink(value: APIWikiPageListItem(
            slug: result.name.lowercased().replacingOccurrences(of: " ", with: "-"),
            title: result.displayName,
            pageType: result.labels.first?.lowercased() ?? "entities",
            tags: result.tags ?? [],
            created: "",
            updated: "",
            protected: false
        )) {
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 6) {
                    Text(result.displayName).font(.body).fontWeight(.bold).foregroundStyle(DesignConstants.primaryText)
                }
                if let preview = result.preview {
                    Text(preview).font(.caption2).foregroundStyle(DesignConstants.secondaryText).lineLimit(2)
                }
                HStack(spacing: 6) {
                    ForEach(result.labels.prefix(3), id: \.self) { label in
                        Text(label).font(.caption2).bold()
                            .padding(.horizontal, 4).padding(.vertical, 1)
                            .background(DesignConstants.systemOrange.opacity(0.12), in: Capsule())
                            .foregroundStyle(DesignConstants.systemOrangeText)
                    }
                    Spacer()
                    Text(String(format: "%.0f%%", result.confidence * 100))
                        .font(.caption2).foregroundStyle(.secondary)
                }
            }
            .padding(.vertical, 4)
        }
    }
}

struct WikiPageCell: View {
    let page: APIWikiPageListItem
    let onDelete: () -> Void

    var body: some View {
        NavigationLink(value: page) {
            WikiPageRow(page: page)
        }
        #if os(macOS)
        .buttonStyle(.plain)
        #endif
        .swipeActions(edge: .trailing, allowsFullSwipe: false) {
            if !page.protected {
                Button("Delete", role: .destructive, action: onDelete)
            }
        }
        .contextMenu {
            if !page.protected {
                Button(role: .destructive, action: onDelete) {
                    Label("Delete", systemImage: "trash")
                }
            }
        }
    }
}

struct WikiPageRow: View {
    let page: APIWikiPageListItem

    var body: some View {
        HStack(spacing: 12) {
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 6) {
                    Text(page.title).font(.body).fontWeight(.bold).foregroundStyle(DesignConstants.primaryText)
                    if page.protected {
                        Image(systemName: "lock.fill").font(.caption2).foregroundStyle(DesignConstants.systemOrange)
                    }
                }
                if !page.tags.isEmpty {
                    Text(page.tags.prefix(3).joined(separator: ", "))
                        .font(.caption2).foregroundStyle(DesignConstants.secondaryText).lineLimit(1)
                }
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 4) {
                Text(page.pageType.capitalized)
                    .font(.caption2).fontWeight(.bold)
                    .padding(.horizontal, 6).padding(.vertical, 2)
                    .background(typeColor(page.pageType).opacity(0.15)).foregroundStyle(typeColor(page.pageType))
                    .clipShape(Capsule())
                if !page.updated.isEmpty {
                    Text(page.updated).font(.caption2).foregroundStyle(DesignConstants.secondaryText)
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

@Observable @MainActor
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

