import SwiftUI

struct EventDetailView: View {
    let event: TemporalEvent

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: DesignConstants.standardPadding) {
                HStack {
                    Image(systemName: eventTypeIcon(event.type))
                        .font(.title3)
                        .foregroundStyle(DesignConstants.systemOrange)
                    Text(event.title)
                        .font(.title2)
                        .bold()
                        .foregroundStyle(DesignConstants.primaryText)
                }

                Label(event.eventDescription, systemImage: "doc.text")
                    .font(.body)
                    .foregroundStyle(DesignConstants.primaryText)
                    .frame(maxWidth: .infinity, alignment: .leading)

                Divider()

                VStack(alignment: .leading, spacing: DesignConstants.compactPadding) {
                    HStack {
                        Label("Confidence", systemImage: "percent")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        Spacer()
                        Text(String(format: "%.0f%% Match", event.confidence * 100))
                            .font(.subheadline)
                            .bold()
                            .foregroundStyle(confidenceColor(event.confidence))
                    }

                    HStack {
                        Label("Type", systemImage: "tag")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        Spacer()
                        Text(event.type.capitalized)
                            .font(.subheadline)
                            .foregroundStyle(DesignConstants.primaryText)
                    }

                    HStack {
                        Label("Date", systemImage: "calendar")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        Spacer()
                        Text(event.timestamp, format: .dateTime.year().month().day())
                            .font(.subheadline)
                            .foregroundStyle(DesignConstants.primaryText)
                    }

                    HStack {
                        Label("Source", systemImage: "bookmark")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        Spacer()
                        Text(event.source)
                            .font(.subheadline)
                            .foregroundStyle(DesignConstants.primaryText)
                    }

                    if let branch = event.branch {
                        HStack {
                            Label("Branch", systemImage: "arrow.triangle.branch")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                            Spacer()
                            Text(branch.name)
                                .font(.subheadline)
                                .foregroundStyle(DesignConstants.systemOrangeText)
                        }
                    }
                }
                .padding()
                .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
            }
            .padding(DesignConstants.standardPadding)
        }
        .background(DesignConstants.warmBackground)
        .navigationTitle("Event Details")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
    }

    private func eventTypeIcon(_ type: String) -> String {
        switch type.lowercased() {
        case "crash": return "flame.fill"
        case "testimony": return "person.fill.viewfinder"
        case "anomaly": return "sparkle.magnifyingglass"
        case "theory": return "lightbulb.fill"
        default: return "doc.text.fill"
        }
    }

    private func confidenceColor(_ confidence: Double) -> Color {
        confidence > 0.9 ? DesignConstants.systemGreenText : DesignConstants.systemOrangeText
    }
}
