// Prints the median face box of a video as JSON (pixels, top-left origin), from every 15th frame.
import AVFoundation
import Vision
import Foundation

let asset = AVURLAsset(url: URL(fileURLWithPath: CommandLine.arguments[1]))
let track = asset.tracks(withMediaType: .video)[0]
let W = Double(track.naturalSize.width), H = Double(track.naturalSize.height)
let reader = try! AVAssetReader(asset: asset)
let out = AVAssetReaderTrackOutput(track: track, outputSettings: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA])
reader.add(out); reader.startReading()
var cx = [Double](), top = [Double](), w = [Double](), h = [Double]()
var n = 0
while let sb = out.copyNextSampleBuffer() {
  defer { n += 1 }
  if n % 15 != 0 { continue }
  guard let pb = CMSampleBufferGetImageBuffer(sb) else { continue }
  let req = VNDetectFaceRectanglesRequest()
  try! VNImageRequestHandler(cvPixelBuffer: pb, options: [:]).perform([req])
  guard let f = req.results?.max(by: { $0.boundingBox.width < $1.boundingBox.width }) else { continue }
  let b = f.boundingBox
  cx.append(b.midX * W); w.append(b.width * W); h.append(b.height * H); top.append((1 - b.maxY) * H)
}
func med(_ a: [Double]) -> Double { let s = a.sorted(); return s.isEmpty ? -1 : s[s.count / 2] }
print(String(format: "{\"samples\": %d, \"cx\": %.1f, \"top\": %.1f, \"w\": %.1f, \"h\": %.1f, \"width\": %.0f, \"height\": %.0f}",
             cx.count, med(cx), med(top), med(w), med(h), W, H))
