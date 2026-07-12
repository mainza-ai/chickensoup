import SwiftUI
import Combine

public struct TaskConsoleView: View {
    let taskId: String
    let taskName: String
    let onFinished: () -> Void
    let onDismiss: () -> Void

    @Environment(AlmanacService.self) private var almanacService
    @State private var taskStatus: APITaskStatus? = nil
    @State private var logs: [String] = []
    @State private var progress: Double = 0.0
    @State private var isFinished = false
    @State private var hasFailed = false
    @State private var errorText = ""
    @State private var elapsed: Double = 0.0

    // Poll timer
    private let timer = Timer.publish(every: 0.5, on: .main, in: .common).autoconnect()

    public init(taskId: String, taskName: String, onFinished: @escaping () -> Void, onDismiss: @escaping () -> Void) {
        self.taskId = taskId
        self.taskName = taskName
        self.onFinished = onFinished
        self.onDismiss = onDismiss
    }

    public var body: some View {
        VStack(spacing: 0) {
            // Header Bar
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(taskName.uppercased())
                        .font(.headline)
                        .bold()
                        .foregroundStyle(DesignConstants.primaryText)
                    
                    HStack(spacing: 8) {
                        Circle()
                            .fill(isFinished ? (hasFailed ? DesignConstants.systemRed : DesignConstants.systemGreen) : DesignConstants.systemOrange)
                            .frame(width: 8, height: 8)
                        
                        Text(isFinished ? (hasFailed ? "Execution Failed" : "Completed Successfully") : "Executing Background Task...")
                            .font(.caption2)
                            .foregroundStyle(DesignConstants.secondaryText)
                        
                        Spacer()
                        
                        Text(String(format: "%.1fs", elapsed))
                            .font(.system(.caption2, design: .monospaced))
                            .foregroundStyle(DesignConstants.secondaryText)
                    }
                }
                
                Spacer()
                
                if isFinished {
                    Button("Done") {
                        onDismiss()
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(hasFailed ? DesignConstants.systemRed : DesignConstants.systemOrange)
                    .bold()
                } else {
                    ProgressView()
                        .progressViewStyle(.circular)
                }
            }
            .padding()
            .background(DesignConstants.cardBackground)
            
            // Progress Bar
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Rectangle()
                        .fill(Color.gray.opacity(0.15))
                    
                    Rectangle()
                        .fill(
                            LinearGradient(
                                colors: hasFailed ? [DesignConstants.systemRed, .red] : [DesignConstants.systemOrange, .purple],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .frame(width: geo.size.width * CGFloat(progress))
                        .animation(.easeInOut(duration: 0.25), value: progress)
                }
            }
            .frame(height: 4)
            
            // Terminal Logs Box
            ScrollViewReader { proxy in
                ScrollView {
                    VStack(alignment: .leading, spacing: 6) {
                        if logs.isEmpty {
                            Text("Waiting for agent response...")
                                .foregroundStyle(DesignConstants.secondaryText)
                        } else {
                            ForEach(0..<logs.count, id: \.self) { idx in
                                let log = logs[idx]
                                Text(log)
                                    .foregroundStyle(
                                        log.contains("ERROR") ? DesignConstants.systemRed :
                                        log.contains("success") || log.contains("succeeded") ? DesignConstants.systemGreenText :
                                        log.contains("Starting") || log.contains("Initializing") ? DesignConstants.systemOrangeText :
                                        DesignConstants.primaryText
                                    )
                                    .id(idx)
                            }
                        }
                    }
                    .font(.system(.caption, design: .monospaced))
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding()
                }
                .background(Color(red: 0.08, green: 0.08, blue: 0.1))
                .onChange(of: logs.count) { _, newCount in
                    if newCount > 0 {
                        withAnimation {
                            proxy.scrollTo(newCount - 1, anchor: .bottom)
                        }
                    }
                }
            }
        }
        .frame(minWidth: 400, minHeight: 300)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .onReceive(timer) { _ in
            guard !isFinished else { return }
            Task {
                if let status = await almanacService.fetchTaskStatus(taskId: taskId) {
                    await MainActor.run {
                        self.taskStatus = status
                        self.logs = status.logs
                        self.progress = status.progress
                        self.elapsed = status.elapsed
                        
                        if status.status == "success" {
                            self.isFinished = true
                            self.progress = 1.0
                            self.timer.upstream.connect().cancel()
                            onFinished()
                        } else if status.status == "failed" {
                            self.isFinished = true
                            self.hasFailed = true
                            self.timer.upstream.connect().cancel()
                        }
                    }
                }
            }
        }
    }
}

// MARK: - Preview

#Preview {
    TaskConsoleView(
        taskId: "preview-task-001",
        taskName: "Preview Pulse Task",
        onFinished: {},
        onDismiss: {}
    )
    .environment(AlmanacService.shared)
    .frame(width: 500, height: 400)
}
