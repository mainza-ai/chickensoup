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
    @Query private var allEntities: [LoreEntity]
    
    @StateObject private var backendService = BackendService.shared
    @State private var searchText = ""
    @State private var showSuggestions = false
    
    var filteredSuggestions: [LoreEntity] {
        if searchText.isEmpty {
            return Array(allEntities.prefix(5))
        } else {
            return allEntities.filter { $0.name.localizedCaseInsensitiveContains(searchText) }
        }
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
                    .font(.caption)
                    .bold()
                    .tracking(2.0)
                    .foregroundStyle(DesignConstants.systemOrangeText)
                
                Spacer()
            }
            .padding(.horizontal, DesignConstants.standardPadding)
            .padding(.top, DesignConstants.standardPadding)
            .padding(.bottom, 8)
            .background(DesignConstants.panelBackground)
            
            // Search Bar header
            VStack(spacing: 0) {
                HStack {
                    // Back button
                    Button(action: {
                        backendService.navigateBack(context: modelContext)
                    }) {
                        Image(systemName: "chevron.left")
                            .font(.system(size: 13, weight: .bold))
                            .foregroundStyle(backendService.canGoBack ? DesignConstants.systemOrangeText : Color.secondary.opacity(0.3))
                    }
                    .buttonStyle(.plain)
                    .disabled(!backendService.canGoBack)
                    
                    // Forward button
                    Button(action: {
                        backendService.navigateForward(context: modelContext)
                    }) {
                        Image(systemName: "chevron.right")
                            .font(.system(size: 13, weight: .bold))
                            .foregroundStyle(backendService.canGoForward ? DesignConstants.systemOrangeText : Color.secondary.opacity(0.3))
                    }
                    .buttonStyle(.plain)
                    .disabled(!backendService.canGoForward)
                    .padding(.trailing, 4)
                    
                    Image(systemName: "magnifyingglass")
                        .foregroundStyle(.secondary)
                    
                    TextField("Search Lore Graph...", text: $searchText, onEditingChanged: { isEditing in
                        withAnimation { showSuggestions = isEditing }
                    })
                    .textFieldStyle(.plain)
                    .onSubmit {
                        if let match = allEntities.first(where: { $0.name.localizedCaseInsensitiveContains(searchText) }) {
                            selectEntity(name: match.name)
                            searchText = ""
                            showSuggestions = false
                        }
                    }
                    
                    if !searchText.isEmpty {
                        Button(action: { searchText = "" }) {
                            Image(systemName: "xmark.circle.fill")
                                .foregroundStyle(.secondary)
                        }
                        .buttonStyle(.plain)
                    }
                    
                    Spacer()
                    
                    if backendService.isFetchingNeighborhood {
                        ProgressView()
                            .scaleEffect(0.8)
                    } else {
                        Button(action: {
                            if !backendService.focusedEntityName.isEmpty {
                                Task {
                                    await backendService.fetchNeighborhood(for: backendService.focusedEntityName, context: modelContext)
                                }
                            } else if let first = allEntities.first {
                                selectEntity(name: first.name)
                            }
                        }) {
                            Image(systemName: "arrow.clockwise")
                                .font(.subheadline)
                                .foregroundStyle(DesignConstants.systemOrangeText)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(DesignConstants.standardPadding)
                .background(.ultraThinMaterial)
                .overlay(
                    VStack {
                        Spacer()
                        Divider()
                    }
                )
                
                // Suggestions dropdown floating overlay inside sidebar frame
                if showSuggestions && !filteredSuggestions.isEmpty {
                    VStack(alignment: .leading, spacing: 0) {
                        ForEach(filteredSuggestions) { entity in
                            Button(action: {
                                selectEntity(name: entity.name)
                                searchText = ""
                                showSuggestions = false
                            }) {
                                HStack {
                                    Text(entity.name.replacingOccurrences(of: "-", with: " ").capitalized)
                                        .font(.subheadline)
                                        .foregroundStyle(DesignConstants.primaryText)
                                    Spacer()
                                    Text(entity.type)
                                        .font(.caption2)
                                        .bold()
                                        .padding(.horizontal, 6)
                                        .padding(.vertical, 2)
                                        .background(DesignConstants.systemOrange.opacity(0.12), in: Capsule())
                                        .foregroundStyle(DesignConstants.systemOrangeText)
                                }
                                .padding(.vertical, 8)
                                .padding(.horizontal, 16)
                                .contentShape(Rectangle())
                            }
                            .buttonStyle(.plain)
                            Divider()
                        }
                    }
                    .background(DesignConstants.cardBackground.opacity(0.95))
                    .background(.ultraThinMaterial)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                    .shadow(color: Color.black.opacity(0.12), radius: 10, x: 0, y: 5)
                    .padding(.horizontal, DesignConstants.standardPadding)
                    .padding(.top, 8)
                    .transition(.move(edge: .top).combined(with: .opacity))
                }
            }
            .zPriority(10)
            
            // Details Scroll Area
            ScrollView {
                if let graph = backendService.neighborhood {
                    VStack(alignment: .leading, spacing: DesignConstants.standardPadding) {
                        // Main entity header info
                        VStack(alignment: .leading, spacing: DesignConstants.compactPadding) {
                            HStack {
                                Text(graph.entity.name.replacingOccurrences(of: "-", with: " ").capitalized)
                                    .font(.title3)
                                    .bold()
                                    .foregroundStyle(DesignConstants.primaryText)
                                
                                Spacer()
                                
                                Text(graph.entity.type)
                                    .font(.caption2)
                                    .bold()
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 2)
                                    .background(DesignConstants.systemOrange.opacity(0.15), in: Capsule())
                                    .foregroundStyle(DesignConstants.systemOrangeText)
                            }
                            
                            Text(graph.entity.summary)
                                .font(.body)
                                .foregroundStyle(DesignConstants.secondaryText)
                                .padding(.top, 4)
                            
                            HStack {
                                Label("Credibility: \(Int(graph.entity.confidence * 100))%", systemImage: "checkmark.shield.fill")
                                    .font(.caption)
                                    .foregroundStyle(DesignConstants.secondaryText)
                                Spacer()
                                Text("Primary Source: \(graph.entity.source)")
                                    .font(.caption)
                                    .foregroundStyle(.tertiary)
                            }
                            .padding(.top, 8)
                        }
                        .padding(DesignConstants.standardPadding)
                        .liquidGlass()
                        
                        // Relationship Connections summary list
                        if !graph.connections.isEmpty {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Active Relationships (\(graph.connections.count))")
                                    .font(.caption)
                                    .bold()
                                    .foregroundStyle(.secondary)
                                
                                ForEach(graph.connections) { conn in
                                    Button {
                                        selectEntity(name: conn.neighbor.name)
                                    } label: {
                                        HStack {
                                            VStack(alignment: .leading, spacing: 2) {
                                                Text(conn.neighbor.name.replacingOccurrences(of: "-", with: " ").capitalized)
                                                    .font(.subheadline)
                                                    .bold()
                                                    .foregroundStyle(DesignConstants.primaryText)
                                                Text(conn.relationshipType.replacingOccurrences(of: "_", with: " "))
                                                    .font(.caption2)
                                                    .foregroundStyle(DesignConstants.systemOrangeText)
                                            }
                                            Spacer()
                                            Text(conn.neighbor.type)
                                                .font(.caption2)
                                                .foregroundStyle(.secondary)
                                                .padding(.horizontal, 6)
                                                .padding(.vertical, 2)
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
                        
                        // Always expanded evidence logs & metrics
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
                        Image(systemName: "circle.grid.hex")
                            .font(.system(size: 40))
                            .foregroundStyle(.secondary)
                        Text("No Entity Selected")
                            .font(.headline)
                            .foregroundStyle(DesignConstants.primaryText)
                        Text("Select a node on the lore graph or search for an entity to view details.")
                            .font(.caption)
                            .foregroundStyle(DesignConstants.secondaryText)
                            .multilineTextAlignment(.center)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.top, 100)
                    .padding(.horizontal)
                }
            }
        }
        .background(DesignConstants.panelBackground)
        .onAppear {
            if backendService.focusedEntityName.isEmpty, let first = allEntities.first {
                selectEntity(name: first.name)
            }
        }
    }
    
    private func selectEntity(name: String) {
        backendService.selectEntity(name, context: modelContext)
    }
}
