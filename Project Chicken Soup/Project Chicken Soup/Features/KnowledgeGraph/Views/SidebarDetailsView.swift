//
//  SidebarDetailsView.swift
//  Project Chicken Soup
//
//  Created by mck on 6/23/26.
//

import SwiftUI
import SwiftData

struct SidebarDetailsView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \LoreEntity.name) private var allEntities: [LoreEntity]
    
    var backendService = BackendService.shared
    @State private var searchText = ""
    @State private var debouncedSearchText = ""
    @State private var showSuggestions = false
    @State private var searchResults: [APISearchResult] = []
    @State private var isSearching = false

    private var filteredSuggestions: [APISearchResult] {
        if debouncedSearchText.isEmpty {
            return searchResults
        }
        return searchResults
    }

    var body: some View {
        VStack(spacing: 0) {
            // App Branding Header
            HStack(spacing: 8) {
                Image("logo")
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .frame(width: 24, height: 24)
                    .clipShape(RoundedRectangle(cornerRadius: 6))

                Text("PROJECT CHICKEN SOUP")
                    .font(.caption).bold().tracking(2.0)
                    .foregroundStyle(DesignConstants.systemOrangeText)

                Spacer()

                Button(action: toggleTheme) {
                    Image(systemName: backendService.config.isDarkMode ? "sun.max.fill" : "moon.fill")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundStyle(DesignConstants.systemOrangeText)
                }
                .buttonStyle(.plain)
            }
            .padding(.horizontal, DesignConstants.standardPadding)
            .padding(.top, DesignConstants.standardPadding)
            .padding(.bottom, 8)
            .background(DesignConstants.panelBackground)

            // Search Bar header
            VStack(spacing: 0) {
                HStack {
                    Button(action: navigateBack) {
                        Image(systemName: "chevron.left")
                            .font(.system(size: 13, weight: .bold))
                            .foregroundStyle(backendService.graph.canGoBack ? DesignConstants.systemOrangeText : Color.secondary.opacity(0.3))
                    }
                    .buttonStyle(.plain)
                    .disabled(!backendService.graph.canGoBack)

                    Button(action: navigateForward) {
                        Image(systemName: "chevron.right")
                            .font(.system(size: 13, weight: .bold))
                            .foregroundStyle(backendService.graph.canGoForward ? DesignConstants.systemOrangeText : Color.secondary.opacity(0.3))
                    }
                    .buttonStyle(.plain)
                    .disabled(!backendService.graph.canGoForward)
                    .padding(.trailing, 4)

                    Image(systemName: "magnifyingglass")
                        .foregroundStyle(.secondary)

                    TextField("Search Lore Graph...", text: $searchText, onEditingChanged: { isEditing in
                        withAnimation { showSuggestions = isEditing }
                    })
                    .textFieldStyle(.plain)
                    .onSubmit {
                        if let first = searchResults.first {
                            selectEntity(name: first.name)
                            searchText = ""
                            showSuggestions = false
                            searchResults = []
                        }
                    }

                    if isSearching {
                        ProgressView().scaleEffect(0.7)
                    } else if !searchText.isEmpty {
                        Button(action: { searchText = ""; searchResults = [] }) {
                            Image(systemName: "xmark.circle.fill")
                                .foregroundStyle(.secondary)
                        }
                        .buttonStyle(.plain)
                    }

                    Spacer()

                    if backendService.graph.isFetchingNeighborhood {
                        ProgressView().scaleEffect(0.8)
                    } else {
                        Button(action: refreshNeighborhood) {
                            Image(systemName: "arrow.clockwise")
                                .font(.subheadline)
                                .foregroundStyle(DesignConstants.systemOrangeText)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(DesignConstants.standardPadding)
                .background(.ultraThinMaterial)
                .overlay(alignment: .bottom) { Divider() }
            }
            .zIndex(10)
            .onChange(of: searchText) { _, newValue in
                Task {
                    try? await Task.sleep(for: .milliseconds(300))
                    if newValue == searchText && !newValue.isEmpty {
                        await performSearch(newValue)
                    } else if newValue.isEmpty {
                        searchResults = []
                    }
                }
            }

            // Details Scroll Area
            ScrollView {
                if let graph = backendService.graph.neighborhood {
                    VStack(alignment: .leading, spacing: DesignConstants.standardPadding) {
                        // Main entity header info
                        VStack(alignment: .leading, spacing: DesignConstants.compactPadding) {
                            HStack {
                                Text(graph.entity.name.replacingOccurrences(of: "-", with: " ").capitalized)
                                    .font(.title3).bold()
                                    .foregroundStyle(DesignConstants.primaryText)
                                Spacer()
                                Text(graph.entity.type)
                                    .font(.caption2).bold()
                                    .padding(.horizontal, 8).padding(.vertical, 2)
                                    .background(DesignConstants.systemOrange.opacity(0.15), in: Capsule())
                                    .foregroundStyle(DesignConstants.systemOrangeText)
                            }
                            Text(graph.entity.summary)
                                .font(.body).foregroundStyle(DesignConstants.secondaryText).padding(.top, 4)
                            HStack {
                                Label("Credibility: \(Int(graph.entity.confidence * 100))%", systemImage: "checkmark.shield.fill")
                                    .font(.caption).foregroundStyle(DesignConstants.secondaryText)
                                Spacer()
                                Text("Primary Source: \(graph.entity.source)")
                                    .font(.caption).foregroundStyle(.tertiary)
                            }
                            .padding(.top, 8)
                        }
                        .padding(DesignConstants.standardPadding)
                        .liquidGlass()

                        if !graph.connections.isEmpty {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Active Relationships (\(graph.connections.count))")
                                    .font(.caption).bold().foregroundStyle(.secondary)
                                ForEach(graph.connections) { conn in
                                    Button { selectEntity(name: conn.neighbor.name) } label: {
                                        HStack {
                                            VStack(alignment: .leading, spacing: 2) {
                                                Text(conn.neighbor.name.replacingOccurrences(of: "-", with: " ").capitalized)
                                                    .font(.subheadline).bold().foregroundStyle(DesignConstants.primaryText)
                                                Text(conn.relationshipType.replacingOccurrences(of: "_", with: " "))
                                                    .font(.caption2).foregroundStyle(DesignConstants.systemOrangeText)
                                            }
                                            Spacer()
                                            Text(conn.neighbor.type)
                                                .font(.caption2).foregroundStyle(.secondary)
                                                .padding(.horizontal, 6).padding(.vertical, 2)
                                                .background(Color.secondary.opacity(0.1), in: Capsule())
                                        }
                                        .padding(10)
                                        .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 8))
                                        .overlay(RoundedRectangle(cornerRadius: 8).stroke(DesignConstants.dividerColor, lineWidth: 1))
                                    }
                                    .buttonStyle(.plain)
                                }
                            }
                        }

                        EvidenceHistoryView(
                            entityName: graph.entity.name,
                            currentConfidence: graph.entity.confidence,
                            currentSummary: graph.entity.summary,
                            currentSource: graph.entity.source
                        )
                    }
                    .padding(DesignConstants.standardPadding)
                } else {
                    VStack(spacing: 12) {
                        Image(systemName: "circle.grid.hex").font(.system(size: 40)).foregroundStyle(.secondary)
                        Text("No Entity Selected").font(.headline).foregroundStyle(DesignConstants.primaryText)
                        Text("Select a node on the lore graph or search for an entity to view details.")
                            .font(.caption).foregroundStyle(DesignConstants.secondaryText)
                            .multilineTextAlignment(.center)
                    }
                    .frame(maxWidth: .infinity).padding(.top, 100).padding(.horizontal)
                }
            }
        }
        .background(DesignConstants.panelBackground)
        .overlay(alignment: .top) {
            if showSuggestions && !filteredSuggestions.isEmpty {
                suggestionsOverlay
            }
        }
    }

    private func performSearch(_ query: String) async {
        isSearching = true
        defer { isSearching = false }
        if let response = await backendService.performSearch(query: query, limit: 10) {
            searchResults = response.results
        }
    }

    private var suggestionsOverlay: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                ForEach(filteredSuggestions) { result in
                    Button(action: {
                        selectEntity(name: result.name)
                        searchText = ""
                        showSuggestions = false
                        searchResults = []
                    }) {
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(result.displayName)
                                    .font(.subheadline)
                                    .foregroundStyle(DesignConstants.primaryText)
                                Text(result.labels.prefix(2).joined(separator: ", "))
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                            }
                            Spacer()
                            Text(String(format: "%.0f%%", result.confidence * 100))
                                .font(.caption2).foregroundStyle(.secondary)
                        }
                        .padding(.vertical, 8).padding(.horizontal, 16)
                        .contentShape(Rectangle())
                    }
                    .buttonStyle(.plain)
                    Divider()
                }
            }
        }
        .frame(maxHeight: 250)
        .background(DesignConstants.cardBackground.opacity(0.95))
        .background(.ultraThinMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .shadow(color: Color.black.opacity(0.12), radius: 10, x: 0, y: 5)
        .padding(.horizontal, DesignConstants.standardPadding)
        .offset(y: 104)
        .zIndex(100)
        .transition(.move(edge: .top).combined(with: .opacity))
    }
    
    private func selectEntity(name: String) {
        backendService.selectEntity(name, context: modelContext)
    }
    
    private func toggleTheme() {
        withAnimation(.spring(response: 0.35, dampingFraction: 0.8)) {
            backendService.config.toggleTheme()
        }
    }
    
    private func navigateBack() {
        backendService.navigateBack(context: modelContext)
    }
    
    private func navigateForward() {
        backendService.navigateForward(context: modelContext)
    }
    
    private func refreshNeighborhood() {
        if !backendService.graph.focusedEntityName.isEmpty {
            Task {
                await backendService.fetchNeighborhood(for: backendService.graph.focusedEntityName, context: modelContext)
            }
        } else if let first = allEntities.first {
            selectEntity(name: first.name)
        }
    }
}
