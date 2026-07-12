import SwiftUI

struct PulseActionGridView: View {
    let wikiEntities: [APIWikiPageListItem]
    let activeTaskId: String?
    let onDryRunTriggered: () -> Void
    let onLiveBriefTriggered: () -> Void
    let onPulseTriggered: (String) -> Void

    private var columns: [GridItem] {
        #if os(macOS)
        [GridItem(.adaptive(minimum: 150))]
        #else
        [GridItem(.adaptive(minimum: 140))]
        #endif
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("QUICK INGESTION INITIATOR")
                    .font(.caption)
                    .bold()
                    .foregroundStyle(DesignConstants.systemOrangeText)
                
                Spacer()
                
                Button(action: onDryRunTriggered) {
                    Label("Almanac Dry Run", systemImage: "doc.text.magnifyingglass")
                        .font(.caption2)
                        .bold()
                        .foregroundStyle(DesignConstants.systemOrange)
                }
                .buttonStyle(.plain)
                .disabled(activeTaskId != nil)
                
                Text("|")
                    .font(.caption2)
                    .foregroundStyle(DesignConstants.dividerColor)
                
                Button(action: onLiveBriefTriggered) {
                    Label("Generate Live Brief", systemImage: "book.pages")
                        .font(.caption2)
                        .bold()
                        .foregroundStyle(.purple)
                }
                .buttonStyle(.plain)
                .disabled(activeTaskId != nil)
            }
            .padding(.horizontal)
            
            if wikiEntities.isEmpty {
                Text("No active wiki entities found in database. Ingest markdown source files first.")
                    .font(.caption2)
                    .foregroundStyle(DesignConstants.secondaryText)
                    .padding()
                    .frame(maxWidth: .infinity, alignment: .center)
                    .background(DesignConstants.cardBackground)
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                    .overlay(RoundedRectangle(cornerRadius: 10).stroke(DesignConstants.glassBorderColor, lineWidth: 1))
                    .padding(.horizontal)
            } else {
                #if os(macOS)
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 12) {
                        ForEach(wikiEntities) { ent in
                            entityButton(for: ent)
                        }
                    }
                    .padding(.horizontal)
                }
                #else
                LazyVGrid(columns: columns, spacing: 12) {
                    ForEach(wikiEntities) { ent in
                        entityButton(for: ent)
                    }
                }
                .padding(.horizontal)
                #endif
            }
        }
    }

    @ViewBuilder
    private func entityButton(for ent: APIWikiPageListItem) -> some View {
        Button(action: {
            onPulseTriggered(ent.slug)
        }) {
            HStack(spacing: 8) {
                VStack(alignment: .leading, spacing: 2) {
                    Text(ent.title)
                        .font(.subheadline)
                        .bold()
                        .foregroundStyle(DesignConstants.primaryText)
                        .lineLimit(1)
                    Text("Slug: \(ent.slug)")
                        .font(.caption2)
                        .foregroundStyle(DesignConstants.secondaryText)
                        .lineLimit(1)
                }
                
                Spacer()
                
                Image(systemName: "bolt.fill")
                    .font(.caption)
                    .foregroundStyle(DesignConstants.systemOrange)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .background(DesignConstants.controlBackground)
            .clipShape(RoundedRectangle(cornerRadius: 10))
            .overlay(RoundedRectangle(cornerRadius: 10).stroke(DesignConstants.glassBorderColor, lineWidth: 1))
        }
        .buttonStyle(.plain)
        .disabled(activeTaskId != nil)
        .accessibilityLabel("Trigger ingestion pulse for \(ent.title)")
    }
}
