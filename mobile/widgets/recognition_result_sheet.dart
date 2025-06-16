import 'package:flutter/material.dart';

class RecognitionResultSheet extends StatelessWidget {
  final List<dynamic>? results;

  RecognitionResultSheet({this.results});

  @override
  Widget build(BuildContext context) {
    // Get the top result if available
    final topResult = results != null && results!.isNotEmpty ? results![0] : null;
    
    return DraggableScrollableSheet(
      initialChildSize: 0.7,
      maxChildSize: 0.9,
      minChildSize: 0.5,
      builder: (context, scrollController) {
        return Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: SingleChildScrollView(
            controller: scrollController,
            child: Padding(
              padding: EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Center(
                    child: Container(
                      width: 40,
                      height: 4,
                      decoration: BoxDecoration(
                        color: Colors.grey[300],
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  ),
                  SizedBox(height: 20),

                  // Song Info
                  Row(
                    children: [
                      Container(
                        width: 100,
                        height: 100,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(12),
                          color: Colors.purple[100],
                        ),
                        child: topResult?['album_image'] != null
                          ? ClipRRect(
                              borderRadius: BorderRadius.circular(12),
                              child: Image.network(
                                topResult!['album_image'],
                                fit: BoxFit.cover,
                                width: 100,
                                height: 100,
                                errorBuilder: (context, error, stackTrace) {
                                  return Icon(Icons.music_note, size: 40, color: Colors.purple);
                                },
                                loadingBuilder: (context, child, loadingProgress) {
                                  if (loadingProgress == null) return child;
                                  return Center(
                                    child: CircularProgressIndicator(
                                      value: loadingProgress.expectedTotalBytes != null
                                          ? loadingProgress.cumulativeBytesLoaded / loadingProgress.expectedTotalBytes!
                                          : null,
                                      color: Colors.purple,
                                    ),
                                  );
                                },
                              ),
                            )
                          : Icon(Icons.music_note, size: 40, color: Colors.purple),
                      ),
                      SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              topResult?['title'] ?? 'Unknown Song',
                              style: TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            Text(
                              topResult?['artist_name'] ?? 'Unknown Artist',
                              style: TextStyle(
                                fontSize: 18,
                                color: Colors.grey[600],
                              ),
                            ),
                            if (topResult?['album_name'] != null)
                              Text(
                                topResult!['album_name'],
                                style: TextStyle(
                                  fontSize: 16,
                                  color: Colors.grey[500],
                                ),
                              ),
                          ],
                        ),
                      ),
                    ],
                  ),

                  SizedBox(height: 30),

                  // Action Buttons
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: () {
                            // TODO: Implement play functionality
                          },
                          icon: Icon(Icons.play_arrow),
                          label: Text('Play'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.purple,
                            foregroundColor: Colors.white,
                            padding: EdgeInsets.symmetric(vertical: 12),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(8),
                            ),
                          ),
                        ),
                      ),
                      SizedBox(width: 12),
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () {
                            // TODO: Implement add to playlist functionality
                          },
                          icon: Icon(Icons.add),
                          label: Text('Add to Playlist'),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: Colors.purple,
                            padding: EdgeInsets.symmetric(vertical: 12),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(8),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),

                  SizedBox(height: 20),

                  // Song Details
                  Text(
                    'Recognition Details',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  SizedBox(height: 12),
                  _buildDetailRow('Song Title', topResult?['title']?.toString() ?? 'N/A'),
                  _buildDetailRow('Confidence', '${((topResult?['probability'] ?? 0) * 100).toStringAsFixed(1)}%'),
                  if (topResult?['similarity'] != null)
                    _buildDetailRow('Similarity Score', '${(topResult['similarity'] * 100).toStringAsFixed(1)}%'),

                  if (results != null && results!.length > 1) ...[
                    SizedBox(height: 30),
                    Text(
                      'Other Possible Matches',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    SizedBox(height: 12),
                    ..._buildOtherMatches(),
                  ],
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(
              color: Colors.grey[600],
              fontSize: 16,
            ),
          ),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.w500,
              fontSize: 16,
            ),
          ),
        ],
      ),
    );
  }

  List<Widget> _buildOtherMatches() {
    if (results == null || results!.length <= 1) return [];
    
    return results!.skip(1).map((result) => ListTile(
      leading: result['album_image'] != null 
        ? ClipRRect(
            borderRadius: BorderRadius.circular(20),
            child: Image.network(
              result['album_image'],
              width: 40,
              height: 40,
              fit: BoxFit.cover,
              errorBuilder: (context, error, stackTrace) {
                return CircleAvatar(
                  backgroundColor: Colors.purple[100],
                  child: Icon(Icons.music_note, color: Colors.purple),
                );
              },
            ),
          )
        : CircleAvatar(
            backgroundColor: Colors.purple[100],
            child: Icon(Icons.music_note, color: Colors.purple),
          ),
      title: Text(result['title'] ?? 'Unknown Song'),
      subtitle: Text('Confidence: ${((result['probability'] ?? 0) * 100).toStringAsFixed(1)}%'),
      trailing: IconButton(
        icon: Icon(Icons.play_arrow),
        onPressed: () {
          // TODO: Implement play functionality
        },
      ),
    )).toList();
  }
}


