import SwiftUI

struct EntanglementMatrixSection: View {
    @Binding var selectedEntityName: String
    let wikiEntities: [APIWikiPageListItem]
    let isFetchingEntanglements: Bool
    let entanglements: [APIEntanglementEntry]
    let divergence: APIDivergenceResult?
    let onEntitySelected: (String) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("SPACETIME ENTANGLEMENT MATRIX")
                .font(.caption)
                .bold()
                .foregroundStyle(DesignConstants.systemOrangeText)
                .padding(.horizontal)
            
            VStack(alignment: .leading, spacing: 16) {
                // Selector
                HStack(spacing: 12) {
                    Text("Explore Connections:")
                        .font(.subheadline)
                        .bold()
                        .foregroundStyle(DesignConstants.primaryText)
                    
                    Picker("Select Entity", selection: $selectedEntityName) {
                        Text("Choose an entity...").tag("")
                        ForEach(wikiEntities) { ent in
                            Text(ent.title).tag(ent.title)
                        }
                    }
                    .pickerStyle(.menu)
                    .onChange(of: selectedEntityName) { _, newValue in
                        onEntitySelected(newValue)
                    }
                    
                    Spacer()
                }
                
                if isFetchingEntanglements {
                    HStack {
                        Spacer()
                        VStack(spacing: 8) {
                            ProgressView()
                            Text("Solving spacetime entanglement equations...")
                                .font(.caption2)
                                .foregroundStyle(DesignConstants.secondaryText)
                        }
                        Spacer()
                    }
                    .padding(.vertical, 20)
                } else if !selectedEntityName.isEmpty {
                    // Divergence card
                    if let div = divergence {
                        #if os(macOS)
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("NARRATIVE DIVERGENCE RISK")
                                    .font(.caption2)
                                    .bold()
                                    .foregroundStyle(DesignConstants.secondaryText)
                                
                                HStack(spacing: 8) {
                                    Text(String(format: "%.1f%%", div.divergenceRisk * 100))
                                        .font(.system(.title3, design: .monospaced))
                                        .bold()
                                        .foregroundStyle(div.divergenceRisk > 0.5 ? DesignConstants.systemRed : DesignConstants.systemGreenText)
                                    
                                    Text(div.divergenceRisk > 0.5 ? "High Risk (Divergent)" : "Low Risk (Stable)")
                                        .font(.caption)
                                        .bold()
                                        .foregroundStyle(div.divergenceRisk > 0.5 ? DesignConstants.systemRed : DesignConstants.systemGreenText)
                                }
                            }
                            
                            Spacer()
                            
                            VStack(alignment: .leading, spacing: 4) {
                                Text("CANON HASH")
                                    .font(.caption2)
                                    .foregroundStyle(DesignConstants.secondaryText)
                                Text(div.canonVectorHash.prefix(8))
                                    .font(.system(.caption2, design: .monospaced))
                            }
                            
                            Spacer()
                            
                            VStack(alignment: .leading, spacing: 4) {
                                Text("LIVE SNAPSHOT HASH")
                                    .font(.caption2)
                                    .foregroundStyle(DesignConstants.secondaryText)
                                Text(div.liveVectorHash.prefix(8))
                                    .font(.system(.caption2, design: .monospaced))
                            }
                        }
                        .padding()
                        .background(DesignConstants.controlBackground)
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                        #else
                        VStack(alignment: .leading, spacing: 12) {
                            HStack(spacing: 8) {
                                Text(String(format: "%.1f%%", div.divergenceRisk * 100))
                                    .font(.system(.title3, design: .monospaced))
                                    .bold()
                                    .foregroundStyle(div.divergenceRisk > 0.5 ? DesignConstants.systemRed : DesignConstants.systemGreenText)
                                Text(div.divergenceRisk > 0.5 ? "High Risk (Divergent)" : "Low Risk (Stable)")
                                    .font(.caption)
                                    .bold()
                                    .foregroundStyle(div.divergenceRisk > 0.5 ? DesignConstants.systemRed : DesignConstants.systemGreenText)
                            }
                            HStack(spacing: 12) {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text("CANON HASH")
                                        .font(.caption2)
                                        .foregroundStyle(DesignConstants.secondaryText)
                                    Text(div.canonVectorHash.prefix(8))
                                        .font(.system(.caption2, design: .monospaced))
                                }
                                Spacer()
                                VStack(alignment: .leading, spacing: 2) {
                                    Text("LIVE SNAPSHOT HASH")
                                        .font(.caption2)
                                        .foregroundStyle(DesignConstants.secondaryText)
                                    Text(div.liveVectorHash.prefix(8))
                                        .font(.system(.caption2, design: .monospaced))
                                }
                            }
                        }
                        .padding()
                        .background(DesignConstants.controlBackground)
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                        #endif
                        
                        if !div.drivingClaims.isEmpty {
                            VStack(alignment: .leading, spacing: 6) {
                                Text("Divergence Drivers (Top claim anomalies):")
                                    .font(.caption)
                                    .bold()
                                    .foregroundStyle(DesignConstants.primaryText)
                                
                                ForEach(div.drivingClaims, id: \.claimText) { claim in
                                    HStack {
                                        Text(claim.claimText)
                                            .font(.caption2)
                                            .foregroundStyle(DesignConstants.primaryText)
                                        
                                        Spacer()
                                        
                                        let oldC = (claim.oldConfidence ?? 0.0) * 100.0
                                        let newC = claim.newConfidence * 100.0
                                        let deltaC = claim.delta * 100.0
                                        Text(String(format: "%.0f%% ➔ %.0f%% (Δ%.0f%%)", oldC, newC, deltaC))
                                            .font(.system(.caption2, design: .monospaced))
                                            .bold()
                                            .foregroundStyle(claim.delta > 0 ? DesignConstants.systemOrangeText : .purple)
                                    }
                                }
                            }
                        }
                    }
                    
                    Divider()
                        .background(DesignConstants.dividerColor)
                    
                    // Connection Matrix
                    if entanglements.isEmpty {
                        Text("No spacetime entanglements above baseline threshold computed.")
                            .font(.caption2)
                            .foregroundStyle(DesignConstants.secondaryText)
                            .frame(maxWidth: .infinity, alignment: .center)
                    } else {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Entangled Spacetime Partners:")
                                .font(.caption)
                                .bold()
                                .foregroundStyle(DesignConstants.primaryText)
                            
                            ForEach(entanglements, id: \.entityB) { ent in
                                HStack {
                                    Image(systemName: "shared.with.you")
                                        .font(.caption)
                                        .foregroundStyle(DesignConstants.systemOrange)
                                    
                                    Text(ent.entityB)
                                        .font(.subheadline)
                                        .bold()
                                        .foregroundStyle(DesignConstants.primaryText)
                                    
                                    Spacer()
                                    
                                    HStack(spacing: 8) {
                                        Text("Co-occurrences: \(ent.coOccurrenceCount)")
                                            .font(.caption2)
                                            .foregroundStyle(DesignConstants.secondaryText)
                                        
                                        Text("Platforms: \(ent.independentPlatforms.joined(separator: ", "))")
                                            .font(.caption2)
                                            .foregroundStyle(DesignConstants.secondaryText)
                                        
                                        Text(String(format: "Entanglement: %.2f", ent.entanglementScore))
                                            .font(.system(.caption, design: .monospaced))
                                            .bold()
                                            .padding(.horizontal, 6)
                                            .padding(.vertical, 2)
                                            .background(DesignConstants.systemOrange.opacity(0.15))
                                            .foregroundStyle(DesignConstants.systemOrangeText)
                                            .clipShape(Capsule())
                                    }
                                }
                                .padding(10)
                                .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 8))
                            }
                        }
                    }
                } else {
                    Text("Select a spacetime entity from the picker above to compute its correlation matrices.")
                        .font(.caption)
                        .foregroundStyle(DesignConstants.secondaryText)
                        .frame(maxWidth: .infinity, alignment: .center)
                        .padding(.vertical, 10)
                }
            }
            .padding()
            .background(DesignConstants.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
            .overlay(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius).stroke(DesignConstants.glassBorderColor, lineWidth: 1))
            .padding(.horizontal)
        }
    }
}
