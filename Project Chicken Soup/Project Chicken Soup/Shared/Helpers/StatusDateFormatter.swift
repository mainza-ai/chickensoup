import Foundation

enum StatusDateFormatter {
    static func format(_ iso: String?) -> String {
        guard let iso, let date = ISO8601DateFormatter().date(from: iso) else { return "\u{2014}" }
        let elapsed = Date.now.timeIntervalSince(date)
        if elapsed < 60 {
            return "\(Int(elapsed))s ago"
        } else if elapsed < 3600 {
            return "\(Int(elapsed / 60))m ago"
        } else if elapsed < 86400 {
            let f = DateFormatter()
            f.dateStyle = .none
            f.timeStyle = .short
            return f.string(from: date)
        }
        let f = DateFormatter()
        f.dateStyle = .medium
        f.timeStyle = .short
        return f.string(from: date)
    }
}
