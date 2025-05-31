<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class StockImage extends Model
{
    protected $fillable = ['stock_id', 'uuid', 'date', 'type', 'dir', 'image'];

    public function stock() {
        return $this->belongsTo(Stock::class);
    }
}
