<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class StockPrice extends Model
{
    protected $fillable = [
        'stock_id', 'uuid', 'date',
        'adj_close', 'close', 'high', 'low', 'open', 'volume'
    ];

    public function stock() {
        return $this->belongsTo(Stock::class);
    }
}
